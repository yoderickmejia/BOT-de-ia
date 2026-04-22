import logging
from datetime import date
from config import settings

logger = logging.getLogger(__name__)


class RiskManager:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.daily_loss = 0.0
        self.daily_loss_date = date.today()
        self.open_positions = 0

    def _reset_daily_loss_if_new_day(self):
        today = date.today()
        if today != self.daily_loss_date:
            self.daily_loss = 0.0
            self.daily_loss_date = today

    def can_trade(self, balance: float) -> tuple[bool, str]:
        self._reset_daily_loss_if_new_day()

        if self.open_positions >= settings.MAX_OPEN_POSITIONS:
            return False, f"Maximo de posiciones abiertas alcanzado ({settings.MAX_OPEN_POSITIONS})"

        max_daily_loss_usd = self.initial_capital * settings.MAX_DAILY_LOSS
        if self.daily_loss >= max_daily_loss_usd:
            return False, f"Perdida diaria maxima alcanzada (${self.daily_loss:.2f})"

        if balance < 10:
            return False, f"Balance insuficiente (${balance:.2f})"

        return True, "OK"

    def calculate_position_size(self, balance: float, entry_price: float, stop_loss_price: float) -> float:
        risk_amount = balance * settings.MAX_RISK_PER_TRADE
        price_risk = entry_price - stop_loss_price

        if price_risk <= 0:
            return 0.0

        size = risk_amount / price_risk
        max_size = (balance * 0.95) / entry_price
        return round(min(size, max_size), 6)

    def register_trade_open(self):
        self.open_positions += 1

    def register_trade_close(self, pnl: float):
        self.open_positions = max(0, self.open_positions - 1)
        if pnl < 0:
            self.daily_loss += abs(pnl)
            logger.info(f"Perdida registrada: ${abs(pnl):.2f} | Perdida diaria total: ${self.daily_loss:.2f}")

    def get_status(self) -> dict:
        self._reset_daily_loss_if_new_day()
        return {
            "open_positions": self.open_positions,
            "daily_loss_usd": round(self.daily_loss, 2),
            "max_daily_loss_usd": round(self.initial_capital * settings.MAX_DAILY_LOSS, 2),
            "daily_loss_remaining": round(
                self.initial_capital * settings.MAX_DAILY_LOSS - self.daily_loss, 2
            ),
        }
