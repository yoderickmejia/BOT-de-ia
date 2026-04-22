import ccxt
import pandas as pd
from config import settings


class ExchangeClient:
    def __init__(self):
        params = {
            "apiKey": settings.BINANCE_API_KEY,
            "secret": settings.BINANCE_API_SECRET,
            "enableRateLimit": True,
        }
        if settings.BINANCE_TESTNET:
            params["options"] = {"defaultType": "spot"}
            self.exchange = ccxt.binance(params)
            self.exchange.set_sandbox_mode(True)
        else:
            self.exchange = ccxt.binance(params)

    def get_price(self, symbol: str) -> float:
        ticker = self.exchange.fetch_ticker(symbol)
        return float(ticker["last"])

    def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("timestamp")
        return df

    def get_balance(self, currency: str = "USDT") -> float:
        balance = self.exchange.fetch_balance()
        return float(balance["free"].get(currency, 0))

    def place_market_order(self, symbol: str, side: str, amount: float) -> dict:
        return self.exchange.create_market_order(symbol, side, amount)

    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> dict:
        return self.exchange.create_limit_order(symbol, side, amount, price)

    def get_open_orders(self, symbol: str) -> list:
        return self.exchange.fetch_open_orders(symbol)

    def cancel_order(self, order_id: str, symbol: str):
        return self.exchange.cancel_order(order_id, symbol)

    def cancel_all_orders(self, symbol: str):
        orders = self.exchange.fetch_open_orders(symbol)
        for order in orders:
            try:
                self.exchange.cancel_order(order["id"], symbol)
            except Exception:
                pass

    def place_oco_order(self, symbol: str, amount: float, stop_loss: float, take_profit: float) -> dict:
        """
        Coloca una orden OCO (One-Cancels-Other) en Binance:
        - Si el precio sube a take_profit -> vende con ganancia
        - Si el precio baja a stop_loss  -> vende con perdida limitada
        Binance cancela la otra automaticamente cuando una se ejecuta.
        """
        return self.exchange.create_order(
            symbol=symbol,
            type="oco",
            side="sell",
            amount=amount,
            price=take_profit,
            params={
                "stopPrice": stop_loss,
                "stopLimitPrice": round(stop_loss * 0.999, 2),
                "stopLimitTimeInForce": "GTC",
            },
        )

    def get_min_order_amount(self, symbol: str) -> float:
        markets = self.exchange.load_markets()
        market = markets.get(symbol, {})
        limits = market.get("limits", {}).get("amount", {})
        return float(limits.get("min", 0.0001))
