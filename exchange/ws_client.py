import asyncio
import ccxt
import pandas as pd
from config import settings


class WSExchangeClient:
    """
    Cliente de mercado en tiempo real.
    Testnet no soporta WebSocket via ccxt.pro, por eso usamos polling
    rapido cada 30 segundos. Para una estrategia de velas de 1h esto
    es practicamente tiempo real (reacciona al cierre de vela en <30s).
    """

    POLL_INTERVAL = 30  # segundos entre cada consulta

    def __init__(self):
        params = {
            "apiKey": settings.BINANCE_API_KEY,
            "secret": settings.BINANCE_API_SECRET,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        }
        self.exchange = ccxt.binance(params)
        if settings.BINANCE_TESTNET:
            self.exchange.set_sandbox_mode(True)

    async def watch_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list:
        await asyncio.sleep(self.POLL_INTERVAL)
        loop = asyncio.get_event_loop()
        ohlcv = await loop.run_in_executor(
            None, lambda: self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        )
        return ohlcv

    def ohlcv_to_df(self, ohlcv: list) -> pd.DataFrame:
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("timestamp")
        return df

    async def close(self):
        pass
