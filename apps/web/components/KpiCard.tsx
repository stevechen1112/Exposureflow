export function KpiCard({
  label,
  value,
  delta,
  suffix,
  note,
}: {
  label: string;
  value: string | number;
  delta?: number;
  suffix?: string;
  note?: string;
}) {
  const deltaClass =
    delta === undefined ? "" : delta >= 0 ? "delta-up" : "delta-down";
  return (
    <div className="card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">
        {value}
        {suffix ? ` ${suffix}` : ""}
      </div>
      {delta !== undefined ? (
        <div className={deltaClass} style={{ fontSize: "0.85rem" }}>
          {delta >= 0 ? "+" : ""}
          {delta}% vs 前 28 天
        </div>
      ) : null}
      {note ? (
        <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: "0.25rem" }}>
          {note}
        </div>
      ) : null}
    </div>
  );
}
