import logging
from exchange.client import ExchangeClient
from risk.manager import RiskManager
from monitor.logger import TradeDB
from notifier.telegram import TelegramNotifier
from strategy.my_strategy import MyStrategy
from config import settings

logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(
        self,
        exchange: ExchangeClient,
        risk: RiskManager,
        db: TradeDB,
        notifier: TelegramNotifier,
        strategy: MyStrategy,
    ):
        self.exchange = exchange
        self.risk = risk
        self.db = db
        self.notifier = notifier
        self.strategy = strategy

    def open_position(self, symbol: str, signal_reason: str) -> bool:
        try:
            balance = self.exchange.get_balance("USDT")
            can, reason = self.risk.can_trade(balance)
            if not can:
                logger.warning(f"Riesgo bloqueo la orden: {reason}")
                return False

            price = self.exchange.get_price(symbol)
            stop_loss = self.strategy.get_stop_loss(price)
            take_profit = self.strategy.get_take_profit(price)
            amount = self.risk.calculate_position_size(balance, price, stop_loss)

            min_amount = self.exchange.get_min_order_amount(symbol)
            if amount < min_amount:
                logger.warning(f"Cantidad calculada {amount} menor al minimo {min_amount}")
                return False

            logger.info(f"Abriendo BUY {symbol} | Precio: {price} | Cantidad: {amount} | SL: {stop_loss} | TP: {take_profit}")
            order = self.exchange.place_market_order(symbol, "buy", amount)

            # Coloca SL y TP como ordenes reales en Binance (OCO).
            # Esto protege la posicion incluso si el bot se cae.
            try:
                self.exchange.place_oco_order(symbol, amount, stop_loss, take_profit)
                logger.info(f"Orden OCO colocada: SL={stop_loss} | TP={take_profit}")
            except Exception as oco_error:
                logger.warning(f"No se pudo colocar OCO (continuando sin ella): {oco_error}")

            trade_id = self.db.open_trade(
                symbol=symbol,
                side="buy",
                entry_price=price,
                amount=amount,
                reason=signal_reason,
            )
            self.risk.register_trade_open()
            self.notifier.trade_opened(symbol, "buy", price, amount, stop_loss, take_profit)

            logger.info(f"Trade abierto. ID: {trade_id} | Order: {order.get('id')}")
            return True

        except Exception as e:
            logger.error(f"Error abriendo posicion: {e}")
            self.notifier.error(f"Error abriendo posicion en {symbol}: {e}")
            return False

    def close_position(self, symbol: str, close_reason: str) -> bool:
        try:
            open_trade = self.db.get_open_trade(symbol)
            if not open_trade:
                logger.info(f"No hay posicion abierta en {symbol}")
                return False

            # Cancela ordenes OCO pendientes antes de cerrar manualmente
            try:
                self.exchange.cancel_all_orders(symbol)
                logger.info("Ordenes OCO pendientes canceladas")
            except Exception as e:
                logger.warning(f"No se pudieron cancelar ordenes: {e}")

            price = self.exchange.get_price(symbol)
            amount = open_trade["amount"]
            entry_price = open_trade["entry_price"]

            logger.info(f"Cerrando posicion {symbol} | Precio: {price} | Razon: {close_reason}")
            self.exchange.place_market_order(symbol, "sell", amount)

            pnl = (price - entry_price) * amount
            pnl_pct = ((price - entry_price) / entry_price) * 100

            self.db.close_trade(open_trade["id"], price, pnl, pnl_pct)
            self.risk.register_trade_close(pnl)
            self.notifier.trade_closed(symbol, entry_price, price, pnl, pnl_pct, close_reason)

            logger.info(f"Trade cerrado. P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
            return True

        except Exception as e:
            logger.error(f"Error cerrando posicion: {e}")
            self.notifier.error(f"Error cerrando posicion en {symbol}: {e}")
            return False
