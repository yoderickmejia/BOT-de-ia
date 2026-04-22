import logging
import requests
from config import settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = bool(self.token and self.chat_id)

    def send(self, message: str):
        if not self.enabled:
            logger.info(f"[Telegram desactivado] {message}")
            return
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            requests.post(url, json={"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        except Exception as e:
            logger.warning(f"Error enviando mensaje Telegram: {e}")

    def trade_opened(self, symbol: str, side: str, price: float, amount: float, sl: float, tp: float):
        emoji = "🟢" if side == "buy" else "🔴"
        self.send(
            f"{emoji} <b>TRADE ABIERTO</b>\n"
            f"Par: {symbol}\n"
            f"Lado: {side.upper()}\n"
            f"Precio entrada: ${price:,.2f}\n"
            f"Cantidad: {amount:.6f}\n"
            f"Stop Loss: ${sl:,.2f}\n"
            f"Take Profit: ${tp:,.2f}"
        )

    def trade_closed(self, symbol: str, entry: float, exit_price: float, pnl: float, pnl_pct: float, reason: str):
        emoji = "✅" if pnl >= 0 else "❌"
        self.send(
            f"{emoji} <b>TRADE CERRADO</b>\n"
            f"Par: {symbol}\n"
            f"Entrada: ${entry:,.2f} → Salida: ${exit_price:,.2f}\n"
            f"P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)\n"
            f"Razon: {reason}"
        )

    def error(self, message: str):
        self.send(f"🚨 <b>ERROR CRITICO</b>\n{message}")

    def daily_summary(self, summary: dict):
        self.send(
            f"📊 <b>RESUMEN DIARIO</b>\n"
            f"Trades: {summary['total_trades']}\n"
            f"Ganados: {summary['wins']} | Perdidos: {summary['losses']}\n"
            f"Win Rate: {summary['win_rate_pct']}%\n"
            f"P&L Total: ${summary['total_pnl_usd']:+.2f}"
        )
