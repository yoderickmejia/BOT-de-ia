import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import pytest
from strategy.my_strategy import MyStrategy


def make_df(closes: list) -> pd.DataFrame:
    n = len(closes)
    df = pd.DataFrame({
        "open": closes,
        "high": [c * 1.01 for c in closes],
        "low": [c * 0.99 for c in closes],
        "close": closes,
        "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="1h"))
    return df


class TestMyStrategy:
    def setup_method(self):
        self.strategy = MyStrategy()

    def test_calculate_indicators_adds_rsi_ema(self):
        closes = [100 + i * 0.5 for i in range(100)]
        df = make_df(closes)
        result = self.strategy.calculate_indicators(df)
        assert "rsi" in result.columns
        assert "ema_fast" in result.columns
        assert "ema_slow" in result.columns

    def test_stop_loss_is_below_entry(self):
        entry = 50000.0
        sl = self.strategy.get_stop_loss(entry)
        assert sl < entry
        assert abs((entry - sl) / entry - 0.02) < 0.001

    def test_take_profit_is_above_entry(self):
        entry = 50000.0
        tp = self.strategy.get_take_profit(entry)
        assert tp > entry
        assert abs((tp - entry) / entry - 0.04) < 0.001

    def test_should_not_buy_insufficient_data(self):
        closes = [100.0] * 10
        df = make_df(closes)
        df = self.strategy.calculate_indicators(df)
        result = self.strategy.should_buy(df)
        assert result is False

    def test_should_sell_on_stop_loss(self):
        closes = [100.0] * 100
        df = make_df(closes)
        df = self.strategy.calculate_indicators(df)
        entry = 100.0
        stop_loss = self.strategy.get_stop_loss(entry)
        df.iloc[-1, df.columns.get_loc("close")] = stop_loss - 0.01
        result = self.strategy.should_sell(df, {"entry_price": entry})
        assert result is True

    def test_should_sell_on_take_profit(self):
        closes = [100.0] * 100
        df = make_df(closes)
        df = self.strategy.calculate_indicators(df)
        entry = 100.0
        take_profit = self.strategy.get_take_profit(entry)
        df.iloc[-1, df.columns.get_loc("close")] = take_profit + 0.01
        result = self.strategy.should_sell(df, {"entry_price": entry})
        assert result is True
