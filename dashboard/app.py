import json
from pathlib import Path

import aiofiles
import aiosqlite
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Trading Bot Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent  # project root
STATUS_FILE = BASE_DIR / "data" / "status.json"
DB_FILE = BASE_DIR / "data" / "trades.db"
TEMPLATE_FILE = Path(__file__).parent / "templates" / "index.html"

DEFAULT_STATUS = {
    "price": 0.0,
    "rsi": 0.0,
    "ema_fast": 0.0,
    "ema_slow": 0.0,
    "open_position": False,
    "last_update": None,
}


@app.get("/", response_class=HTMLResponse)
async def index():
    async with aiofiles.open(TEMPLATE_FILE, encoding="utf-8") as f:
        html = await f.read()
    return HTMLResponse(content=html)


@app.get("/api/status")
async def get_status():
    try:
        async with aiofiles.open(STATUS_FILE, encoding="utf-8") as f:
            data = json.loads(await f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        data = DEFAULT_STATUS.copy()
    return JSONResponse(content=data)


@app.get("/api/trades")
async def get_trades():
    query = """
        SELECT id, symbol, side, entry_price, exit_price, amount,
               pnl, pnl_pct, reason, opened_at, closed_at, status
        FROM trades
        ORDER BY id DESC
        LIMIT 50
    """
    cols = ["id", "symbol", "side", "entry_price", "exit_price", "amount",
            "pnl", "pnl_pct", "reason", "opened_at", "closed_at", "status"]
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
        trades = [dict(zip(cols, row)) for row in rows]
    except Exception:
        trades = []
    return JSONResponse(content=trades)


@app.get("/api/summary")
async def get_summary():
    query = """
        SELECT
            COUNT(*) AS total_trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) AS losses,
            ROUND(SUM(pnl), 4) AS total_pnl
        FROM trades
        WHERE status = 'closed'
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute(query) as cursor:
                row = await cursor.fetchone()
        total, wins, losses, total_pnl = row if row else (0, 0, 0, 0.0)
        total = total or 0
        wins = wins or 0
        losses = losses or 0
        total_pnl = total_pnl or 0.0
        win_rate = round((wins / total * 100), 2) if total > 0 else 0.0
    except Exception:
        total, wins, losses, total_pnl, win_rate = 0, 0, 0, 0.0, 0.0
    return JSONResponse(content={
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "total_pnl": total_pnl,
        "win_rate": win_rate,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=8080, reload=False)
