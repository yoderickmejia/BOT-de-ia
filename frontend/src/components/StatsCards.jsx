export default function StatsCards({ summary }) {
  const total = summary?.total_trades ?? 0;
  const wins = summary?.wins ?? 0;
  const losses = summary?.losses ?? 0;
  const winRate = summary?.win_rate ?? 0;
  const pnl = summary?.total_pnl ?? 0;

  return (
    <div className="cards">
      <div className="card">
        <div className="card-label">Total Trades</div>
        <div className="card-value blue">{total}</div>
        <div className="card-sub">{wins} ganados · {losses} perdidos</div>
      </div>

      <div className="card">
        <div className="card-label">Win Rate</div>
        <div className={`card-value ${winRate >= 50 ? "green" : "red"}`}>
          {winRate.toFixed(1)}%
        </div>
        <div className="card-sub">de {total} operaciones cerradas</div>
      </div>

      <div className="card">
        <div className="card-label">P&L Total</div>
        <div className={`card-value ${pnl >= 0 ? "green" : "red"}`}>
          {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
        </div>
        <div className="card-sub">ganancia / perdida acumulada</div>
      </div>
    </div>
  );
}
