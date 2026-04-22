import os
from dotenv import load_dotenv

load_dotenv()

# Exchange
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_TESTNET = os.getenv("BINANCE_TESTNET", "true").lower() == "true"

# Trading
TRADING_PAIR = os.getenv("TRADING_PAIR", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "1000"))

# Riesgo
MAX_RISK_PER_TRADE = float(os.getenv("MAX_RISK_PER_TRADE", "0.01"))
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "0.03"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "1"))

# Notificaciones
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Base de datos
DB_PATH = os.getenv("DB_PATH", "data/trades.db")

# Estrategia RSI + EMA (parametros ajustables)
RSI_PERIOD = 14
RSI_OVERSOLD = 35       # Compra cuando RSI baja de aqui
RSI_OVERBOUGHT = 65     # Vende cuando RSI sube de aqui
EMA_FAST = 20
EMA_SLOW = 50
STOP_LOSS_PCT = 0.02    # 2% de perdida maxima por trade
TAKE_PROFIT_PCT = 0.04  # 4% de ganancia objetivo
