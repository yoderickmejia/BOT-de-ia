import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from risk.manager import RiskManager
from config import settings


class TestRiskManager:
    def setup_method(self):
        self.risk = RiskManager(initial_capital=1000)

    def test_can_trade_with_sufficient_balance(self):
        ok, reason = self.risk.can_trade(500)
        assert ok is True

    def test_cannot_trade_with_low_balance(self):
        ok, reason = self.risk.can_trade(5)
        assert ok is False
        assert "insuficiente" in reason.lower()

    def test_cannot_trade_when_max_positions_reached(self):
        self.risk.open_positions = settings.MAX_OPEN_POSITIONS
        ok, reason = self.risk.can_trade(500)
        assert ok is False
        assert "posiciones" in reason.lower()

    def test_cannot_trade_when_daily_loss_exceeded(self):
        self.risk.daily_loss = 1000 * settings.MAX_DAILY_LOSS + 1
        ok, reason = self.risk.can_trade(500)
        assert ok is False
        assert "diaria" in reason.lower()

    def test_position_size_respects_risk(self):
        balance = 1000
        entry = 50000
        stop = 49000
        size = self.risk.calculate_position_size(balance, entry, stop)
        max_loss = size * (entry - stop)
        assert max_loss <= balance * settings.MAX_RISK_PER_TRADE * 1.01

    def test_position_size_zero_on_invalid_stop(self):
        size = self.risk.calculate_position_size(1000, 50000, 50000)
        assert size == 0.0

    def test_register_trade_close_increases_daily_loss_on_loss(self):
        self.risk.register_trade_close(-50)
        assert self.risk.daily_loss == 50

    def test_register_trade_close_no_effect_on_profit(self):
        self.risk.register_trade_close(50)
        assert self.risk.daily_loss == 0
