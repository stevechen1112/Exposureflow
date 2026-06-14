export function ExposureFlowLogo() {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "0.45rem", fontWeight: 700 }}>
      <span
        aria-hidden
        style={{
          width: 22,
          height: 22,
          borderRadius: 6,
          background: "linear-gradient(135deg, #2563eb 0%, #38bdf8 100%)",
          boxShadow: "0 2px 6px rgba(37, 99, 235, 0.35)",
        }}
      />
      <span style={{ letterSpacing: "-0.02em" }}>ExposureFlow</span>
    </span>
  );
}
