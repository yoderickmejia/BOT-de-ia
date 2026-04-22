"""
Backtester simple: prueba la estrategia con datos historicos de Binance.
Uso: python -m backtester.backtest
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ccxt
import pandas as pd
import ta
from config import settings
from strategy.my_strategy import MyStrategy


def fetch_historical_data(symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
    exchange = ccxt.binance({"enableRateLimit": True})
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")
    return df


def run_backtest(symbol: str = None, timeframe: str = None, initial_capital: float = None):
    symbol = symbol or settings.TRADING_PAIR
    timeframe = timeframe or settings.TIMEFRAME
    initial_capital = initial_capital or settings.INITIAL_CAPITAL

    print(f"\n{'='*50}")
    print(f"BACKTESTING: {symbol} | {timeframe} | Capital: ${initial_capital}")
    print(f"Estrategia: RSI({settings.RSI_PERIOD}) + EMA({settings.EMA_FAST}/{settings.EMA_SLOW})")
    print(f"Stop Loss: {settings.STOP_LOSS_PCT*100}% | Take Profit: {settings.TAKE_PROFIT_PCT*100}%")
    print(f"{'='*50}\n")

    print("Descargando datos historicos de Binance...")
    df = fetch_historical_data(symbol, timeframe, limit=500)
    strategy = MyStrategy()
    df = strategy.calculate_indicators(df)
    df = df.dropna()

    capital = initial_capital
    position = None
    trades = []

    for i in range(settings.EMA_SLOW + 5, len(df)):
        window = df.iloc[:i+1]
        last = df.iloc[i]
        current_price = last["close"]

        if position is None:
            if strategy.should_buy(window):
                stop_loss = strategy.get_stop_loss(current_price)
                take_profit = strategy.get_take_profit(current_price)
                risk_amount = capital * settings.MAX_RISK_PER_TRADE
                size = risk_amount / (current_price - stop_loss)
                size = min(size, (capital * 0.95) / current_price)

                position = {
                    "entry_price": current_price,
                    "amount": size,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "entry_time": df.index[i],
                }
        else:
            sl_hit = current_price <= position["stop_loss"]
            tp_hit = current_price >= position["take_profit"]
            sell_signal = strategy.should_sell(window, {"entry_price": position["entry_price"]})

            if sl_hit or tp_hit or sell_signal:
                exit_price = current_price
                pnl = (exit_price - position["entry_price"]) * position["amount"]
                pnl_pct = (exit_price - position["entry_price"]) / position["entry_price"] * 100
                capital += pnl

                reason = "Stop Loss" if sl_hit else ("Take Profit" if tp_hit else "Señal venta")
                trades.append({
                    "entry": position["entry_price"],
                    "exit": exit_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "reason": reason,
                    "entry_time": position["entry_time"],
                    "exit_time": df.index[i],
                })
                position = None

    if not trades:
        print("No se generaron trades en el periodo analizado.")
        return

    trades_df = pd.DataFrame(trades)
    wins = trades_df[trades_df["pnl"] > 0]
    losses = trades_df[trades_df["pnl"] <= 0]

    total_pnl = trades_df["pnl"].sum()
    win_rate = len(wins) / len(trades_df) * 100
    avg_win = wins["pnl"].mean() if len(wins) > 0 else 0
    avg_loss = losses["pnl"].mean() if len(losses) > 0 else 0
    profit_factor = abs(wins["pnl"].sum() / losses["pnl"].sum()) if len(losses) > 0 and losses["pnl"].sum() != 0 else float("inf")

    running_capital = initial_capital
    peak = initial_capital
    max_drawdown = 0
    for pnl in trades_df["pnl"]:
        running_capital += pnl
        if running_capital > peak:
            peak = running_capital
        dd = (peak - running_capital) / peak * 100
        if dd > max_drawdown:
            max_drawdown = dd

    print(f"Periodo: {df.index[0].date()} -> {df.index[-1].date()}")
    print(f"Total de trades: {len(trades_df)}")
    print(f"Ganados: {len(wins)} | Perdidos: {len(losses)}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"P&L Total: ${total_pnl:+.2f}")
    print(f"Capital Final: ${capital:.2f} ({(capital/initial_capital-1)*100:+.1f}%)")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Max Drawdown: {max_drawdown:.1f}%")
    print(f"Promedio ganancia: ${avg_win:.2f} | Promedio perdida: ${avg_loss:.2f}")
    print(f"\n{'='*50}")

    return trades_df


if __name__ == "__main__":
    run_backtest()
