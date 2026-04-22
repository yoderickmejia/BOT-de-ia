import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";

export default function PnLChart({ trades }) {
  const closed = [...trades]
    .filter((t) => t.status === "closed" && t.pnl != null)
    .reverse();

  if (closed.length === 0) {
    return <div className="empty-state">Sin trades cerrados todavia</div>;
  }

  let cumulative = 0;
  const data = closed.map((t, i) => {
    cumulative += t.pnl;
    return {
      name: `#${i + 1}`,
      pnl: parseFloat(cumulative.toFixed(2)),
    };
  });

  const isPositive = data[data.length - 1].pnl >= 0;
  const color = isPositive ? "#22c55e" : "#ef4444";

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" />
        <XAxis dataKey="name" tick={{ fill: "#475569", fontSize: 11 }} />
        <YAxis
          tick={{ fill: "#475569", fontSize: 11 }}
          tickFormatter={(v) => `$${v}`}
        />
        <Tooltip
          contentStyle={{ background: "#0b0f19", border: "1px solid #1e2d45", borderRadius: 8 }}
          labelStyle={{ color: "#94a3b8" }}
          formatter={(v) => [`$${v.toFixed(2)}`, "P&L acumulado"]}
        />
        <ReferenceLine y={0} stroke="#334155" strokeDasharray="4 4" />
        <Line
          type="monotone"
          dataKey="pnl"
          stroke={color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: color }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
