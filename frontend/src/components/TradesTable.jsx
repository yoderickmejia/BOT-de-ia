export default function TradesTable({ trades }) {
  if (trades.length === 0) {
    return <div className="empty-state">No hay trades registrados todavia</div>;
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Par</th>
            <th>Entrada</th>
            <th>Salida</th>
            <th>P&L ($)</th>
            <th>P&L (%)</th>
            <th>Razon</th>
            <th>Estado</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t) => {
            const isOpen = t.status === "open";
            const pnlPositive = (t.pnl ?? 0) >= 0;
            return (
              <tr key={t.id}>
                <td style={{ color: "#475569" }}>{t.id}</td>
                <td style={{ color: "#38bdf8", fontWeight: 600 }}>{t.symbol}</td>
                <td>${t.entry_price?.toLocaleString("es") ?? "—"}</td>
                <td>{t.exit_price ? `$${t.exit_price.toLocaleString("es")}` : "—"}</td>
                <td className={isOpen ? "" : pnlPositive ? "pnl-positive" : "pnl-negative"}>
                  {isOpen ? "—" : `${pnlPositive ? "+" : ""}$${t.pnl?.toFixed(2)}`}
                </td>
                <td className={isOpen ? "" : pnlPositive ? "pnl-positive" : "pnl-negative"}>
                  {isOpen ? "—" : `${pnlPositive ? "+" : ""}${t.pnl_pct?.toFixed(2)}%`}
                </td>
                <td style={{ color: "#94a3b8", fontSize: "0.82rem", maxWidth: 200 }}>
                  {t.reason ?? "—"}
                </td>
                <td>
                  <span className={`badge ${isOpen ? "badge-open" : "badge-closed"}`}>
                    {isOpen ? "Abierto" : "Cerrado"}
                  </span>
                </td>
                <td style={{ color: "#475569", fontSize: "0.82rem" }}>
                  {t.opened_at ? new Date(t.opened_at).toLocaleString("es") : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
