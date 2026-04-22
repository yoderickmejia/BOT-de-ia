"""
Estrategia: RSI + EMA Crossover (nivel principiante)

Logica simplificada:
  COMPRA  -> RSI < 35  (el mercado esta "barato" / sobrevendido)
             Y precio esta por encima de EMA50 (tendencia alcista)
  VENTA   -> RSI > 65  (el mercado esta "caro" / sobrecomprado)
             O precio cae por debajo de EMA50 (tendencia cambio)
  Stop Loss   : 2% por debajo del precio de entrada
  Take Profit : 4% por encima del precio de entrada
"""

import pandas as pd
import ta
from config import settings


class MyStrategy:
    def __init__(self):
        self.rsi_period = settings.RSI_PERIOD
        self.rsi_oversold = settings.RSI_OVERSOLD
        self.rsi_overbought = settings.RSI_OVERBOUGHT
        self.ema_fast = settings.EMA_FAST
        self.ema_slow = settings.EMA_SLOW
        self.stop_loss_pct = settings.STOP_LOSS_PCT
        self.take_profit_pct = settings.TAKE_PROFIT_PCT

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["rsi"] = ta.momentum.RSIIndicator(close=df["close"], window=self.rsi_period).rsi()
        df["ema_fast"] = ta.trend.EMAIndicator(close=df["close"], window=self.ema_fast).ema_indicator()
        df["ema_slow"] = ta.trend.EMAIndicator(close=df["close"], window=self.ema_slow).ema_indicator()
        return df

    def should_buy(self, df: pd.DataFrame) -> bool:
        if len(df) < self.ema_slow + 5:
            return False

        last = df.iloc[-1]
        prev = df.iloc[-2]

        rsi_oversold = last["rsi"] < self.rsi_oversold
        price_above_ema_slow = last["close"] > last["ema_slow"]

        # EMA rapida cruzando hacia arriba a EMA lenta (golden cross local)
        ema_cross_up = (
            prev["ema_fast"] <= prev["ema_slow"]
            and last["ema_fast"] > last["ema_slow"]
        )

        # Condicion principal: RSI barato + tendencia alcista
        return rsi_oversold and price_above_ema_slow

    def should_sell(self, df: pd.DataFrame, position: dict) -> bool:
        if len(df) < 2:
            return False

        last = df.iloc[-1]
        entry_price = position.get("entry_price", 0)

        rsi_overbought = last["rsi"] > self.rsi_overbought
        price_below_ema_slow = last["close"] < last["ema_slow"]

        stop_loss_hit = last["close"] <= self.get_stop_loss(entry_price)
        take_profit_hit = last["close"] >= self.get_take_profit(entry_price)

        return rsi_overbought or price_below_ema_slow or stop_loss_hit or take_profit_hit

    def get_stop_loss(self, entry_price: float) -> float:
        return round(entry_price * (1 - self.stop_loss_pct), 2)

    def get_take_profit(self, entry_price: float) -> float:
        return round(entry_price * (1 + self.take_profit_pct), 2)

    def get_signal_reason(self, df: pd.DataFrame) -> str:
        last = df.iloc[-1]
        return (
            f"RSI={last['rsi']:.1f} | "
            f"EMA{self.ema_fast}={last['ema_fast']:.2f} | "
            f"EMA{self.ema_slow}={last['ema_slow']:.2f} | "
            f"Precio={last['close']:.2f}"
        )
