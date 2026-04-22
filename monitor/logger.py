import logging
import os
import sqlite3
from datetime import datetime
from config import settings

os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/bot.log", encoding="utf-8"),
    ],
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class TradeDB:
    def __init__(self, db_path: str = settings.DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL,
                    exit_price REAL,
                    amount REAL,
                    pnl REAL,
                    pnl_pct REAL,
                    reason TEXT,
                    opened_at TEXT,
                    closed_at TEXT,
                    status TEXT DEFAULT 'open'
                )
            """)

    def open_trade(self, symbol: str, side: str, entry_price: float, amount: float, reason: str = "") -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO trades (symbol, side, entry_price, amount, reason, opened_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'open')""",
                (symbol, side, entry_price, amount, reason, datetime.utcnow().isoformat()),
            )
            return cursor.lastrowid

    def close_trade(self, trade_id: int, exit_price: float, pnl: float, pnl_pct: float):
        with self._connect() as conn:
            conn.execute(
                """UPDATE trades SET exit_price=?, pnl=?, pnl_pct=?, closed_at=?, status='closed'
                   WHERE id=?""",
                (exit_price, pnl, pnl_pct, datetime.utcnow().isoformat(), trade_id),
            )

    def get_open_trade(self, symbol: str) -> dict | None:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM trades WHERE symbol=? AND status='open' ORDER BY id DESC LIMIT 1",
                (symbol,),
            ).fetchone()
            return dict(row) if row else None

    def get_summary(self) -> dict:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
                    ROUND(SUM(pnl), 2) as total_pnl
                FROM trades WHERE status='closed'
            """).fetchone()
            total, wins, losses, total_pnl = row
            win_rate = round((wins / total * 100), 1) if total else 0
            return {
                "total_trades": total or 0,
                "wins": wins or 0,
                "losses": losses or 0,
                "win_rate_pct": win_rate,
                "total_pnl_usd": total_pnl or 0,
            }
