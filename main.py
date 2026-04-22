"""
Trading Bot - Tiempo Real via WebSocket
Estrategia: RSI + EMA Crossover
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from config import settings
from exchange.client import ExchangeClient
from exchange.ws_client import WSExchangeClient
from strategy.my_strategy import MyStrategy
from risk.manager import RiskManager
from executor.order_executor import OrderExecutor
from monitor.logger import TradeDB, get_logger
from notifier.telegram import TelegramNotifier

logger = get_logger("main")

STATUS_FILE = os.path.join("data", "status.json")


def _write_status(price: float, rsi: float = 0.0, ema_fast: float = 0.0, ema_slow: float = 0.0, has_position: bool = False):
    os.makedirs("data", exist_ok=True)
    data = {
        "price": round(price, 2),
        "rsi": round(rsi, 2),
        "ema_fast": round(ema_fast, 2),
        "ema_slow": round(ema_slow, 2),
        "open_position": has_position,
        "last_update": datetime.now(timezone.utc).isoformat(),
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)


def build_components():
    exchange = ExchangeClient()
    ws = WSExchangeClient()
    strategy = MyStrategy()
    risk = RiskManager(initial_capital=settings.INITIAL_CAPITAL)
    db = TradeDB()
    notifier = TelegramNotifier()
    executor = OrderExecutor(exchange, risk, db, notifier, strategy)
    return exchange, ws, strategy, risk, db, notifier, executor


async def trading_loop(ws: WSExchangeClient, strategy: MyStrategy, executor: OrderExecutor, db: TradeDB):
    symbol = settings.TRADING_PAIR
    timeframe = settings.TIMEFRAME
    prev_candle_time = None

    logger.info(f"Monitoreo activo | {symbol} | {timeframe} | consulta cada 30s")
    logger.info("Esperando datos del mercado...")

    while True:
        try:
            ohlcv = await ws.watch_candles(symbol, timeframe, limit=200)

            if not ohlcv or len(ohlcv) < 60:
                continue

            current_candle_time = ohlcv[-1][0]

            # Log de estado en cada consulta (cada 30s)
            last_raw = ohlcv[-1]
            current_price = last_raw[4]
            logger.info(f"Mercado activo | Precio=${current_price:,.2f} | Esperando cierre de vela...")

            # Escribe status.json para el dashboard (sin indicadores aun)
            open_trade = db.get_open_trade(symbol)
            _write_status(current_price, has_position=bool(open_trade))

            # Solo evaluamos la estrategia cuando cierra una vela (empieza una nueva)
            if prev_candle_time is not None and current_candle_time != prev_candle_time:
                # Usamos todas las velas excepto la ultima (que aun esta formandose)
                closed_candles = ohlcv[:-1]
                df = ws.ohlcv_to_df(closed_candles)
                df = strategy.calculate_indicators(df)
                df = df.dropna()

                if len(df) < 60:
                    prev_candle_time = current_candle_time
                    continue

                open_trade = db.get_open_trade(symbol)
                last = df.iloc[-1]

                # Actualiza status.json con indicadores reales al cierre de vela
                _write_status(
                    price=float(last["close"]),
                    rsi=float(last["rsi"]),
                    ema_fast=float(last["ema_fast"]),
                    ema_slow=float(last["ema_slow"]),
                    has_position=bool(open_trade),
                )

                if open_trade:
                    position = {"entry_price": open_trade["entry_price"]}
                    if strategy.should_sell(df, position):
                        reason = strategy.get_signal_reason(df)
                        logger.info(f"VENTA | {reason}")
                        executor.close_position(symbol, reason)
                    else:
                        entry = open_trade["entry_price"]
                        pnl_pct = (last["close"] - entry) / entry * 100
                        logger.info(
                            f"Posicion activa | Entrada: ${entry:.2f} | "
                            f"Actual: ${last['close']:.2f} | P&L: {pnl_pct:+.2f}% | "
                            f"RSI: {last['rsi']:.1f}"
                        )
                else:
                    if strategy.should_buy(df):
                        reason = strategy.get_signal_reason(df)
                        logger.info(f"COMPRA | {reason}")
                        executor.open_position(symbol, reason)
                    else:
                        logger.info(
                            f"Sin senal | RSI={last['rsi']:.1f} | "
                            f"Precio=${last['close']:.2f} | "
                            f"EMA{settings.EMA_SLOW}=${last['ema_slow']:.2f}"
                        )

            prev_candle_time = current_candle_time

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error en loop: {e}", exc_info=True)
            await asyncio.sleep(5)


async def main():
    logger.info("=" * 50)
    logger.info("TRADING BOT - TIEMPO REAL (WebSocket)")
    logger.info(f"Par: {settings.TRADING_PAIR} | Timeframe: {settings.TIMEFRAME}")
    logger.info(f"Testnet: {settings.BINANCE_TESTNET} | Capital: ${settings.INITIAL_CAPITAL}")
    logger.info("=" * 50)

    if not settings.BINANCE_API_KEY or settings.BINANCE_API_KEY == "tu_api_key_aqui":
        logger.error("ERROR: Configura tus API keys en el archivo .env")
        return

    _, ws, strategy, _, db, notifier, executor = build_components()

    notifier.send(
        "🤖 <b>Bot iniciado (tiempo real)</b>\n"
        f"Par: {settings.TRADING_PAIR} | {settings.TIMEFRAME}\n"
        f"Testnet: {settings.BINANCE_TESTNET}"
    )

    try:
        await trading_loop(ws, strategy, executor, db)
    except KeyboardInterrupt:
        logger.info("Deteniendo bot...")
    finally:
        summary = db.get_summary()
        logger.info(f"Resumen: {summary}")
        notifier.daily_summary(summary)
        await ws.close()
        logger.info("Bot detenido correctamente.")


if __name__ == "__main__":
    asyncio.run(main())
