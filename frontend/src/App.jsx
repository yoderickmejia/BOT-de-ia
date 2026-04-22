import { useState, useEffect } from "react";
import StatsCards from "./components/StatsCards";
import PnLChart from "./components/PnLChart";
import TradesTable from "./components/TradesTable";

const REFRESH_MS = 10_000;

function isOnline(lastUpdate) {
  if (!lastUpdate) return false;
  return (Date.now() - new Date(lastUpdate).getTime()) < 60_000;
}

export default function App() {
  const [status, setStatus] = useState(null);
  const [summary, setSummary] = useState(null);
  const [trades, setTrades] = useState([]);

  async function fetchAll() {
    try {
      const [s, sum, t] = await Promise.all([
        fetch("/api/status").then((r) => r.json()),
        fetch("/api/summary").then((r) => r.json()),
        fetch("/api/trades").then((r) => r.json()),
      ]);
      setStatus(s);
      setSummary(sum);
      setTrades(t);
    } catch (_) {}
  }

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, REFRESH_MS);
    return () => clearInterval(id);
  }, []);

  const online = isOnline(status?.last_update);

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="header">
        <h1>Trading Bot Dashboard</h1>
        <div className="header-right">
          <div className="status-badge">
            <div className={`status-dot ${online ? "online" : "offline"}`} />
            {online ? "Bot activo" : "Bot offline"}
          </div>
          {status?.last_update && (
            <span className="last-update">
              Actualizado: {new Date(status.last_update).toLocaleTimeString("es")}
            </span>
          )}
        </div>
      </div>

      {/* Market bar */}
      <div className="market-bar">
        <div className="market-item">
          <label>Precio BTC</label>
          <span>${status?.price?.toLocaleString("es") ?? "—"}</span>
        </div>
        <div className="market-item">
          <label>RSI (14)</label>
          <span className="rsi-value">{status?.rsi?.toFixed(1) ?? "—"}</span>
        </div>
        <div className="market-item">
          <label>EMA 20</label>
          <span>${status?.ema_fast?.toLocaleString("es") ?? "—"}</span>
        </div>
        <div className="market-item">
          <label>EMA 50</label>
          <span>${status?.ema_slow?.toLocaleString("es") ?? "—"}</span>
        </div>
        <div className="market-item">
          <label>Posicion abierta</label>
          <span style={{ color: status?.open_position ? "#22c55e" : "#64748b" }}>
            {status?.open_position ? "SI" : "No"}
          </span>
        </div>
      </div>

      {/* Stats cards */}
      <StatsCards summary={summary} />

      {/* Chart */}
      <div className="chart-section">
        <div className="section-title">P&L Acumulado</div>
        <PnLChart trades={trades} />
      </div>

      {/* Trades table */}
      <div className="trades-section">
        <div className="section-title">Historial de Trades</div>
        <TradesTable trades={trades} />
      </div>
    </div>
  );
}
