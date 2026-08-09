import React from "react";

export default function GlobalLoading() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label="Carregando plataforma Ontrackchain"
      style={{
        minHeight: "100vh",
        padding: "3rem 1.5rem",
        fontFamily: "system-ui, sans-serif",
        background:
          "linear-gradient(180deg, #0b1220 0%, #0f172a 100%)",
        color: "#cbd5e1",
      }}
    >
      <div style={{ maxWidth: "72rem", margin: "0 auto" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "1rem",
            marginBottom: "2rem",
          }}
        >
          <div
            aria-hidden="true"
            style={{
              width: "3rem",
              height: "3rem",
              borderRadius: "0.75rem",
              background:
                "linear-gradient(135deg, #6366f1 0%, #0ea5e9 100%)",
              animation: "otcPulse 1.6s ease-in-out infinite",
            }}
          />
          <div>
            <div
              aria-hidden="true"
              style={{
                width: "14rem",
                height: "1.25rem",
                borderRadius: "0.5rem",
                background: "#1f2937",
                marginBottom: "0.5rem",
                animation: "otcShimmer 1.8s linear infinite",
              }}
            />
            <div
              aria-hidden="true"
              style={{
                width: "9rem",
                height: "0.85rem",
                borderRadius: "0.5rem",
                background: "#111827",
                animation: "otcShimmer 1.8s linear infinite",
              }}
            />
          </div>
        </div>

        <div
          role="list"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(18rem, 1fr))",
            gap: "1rem",
          }}
        >
          {[0, 1, 2, 3].map((i) => (
            <div
              role="listitem"
              key={i}
              aria-label={`Skeleton de card ${i + 1} de 4`}
              style={{
                padding: "1.5rem",
                borderRadius: "0.75rem",
                border: "1px solid #1f2937",
                background: "rgba(17, 24, 39, 0.85)",
              }}
            >
              <div
                aria-hidden="true"
                style={{
                  width: "40%",
                  height: "0.85rem",
                  borderRadius: "0.3rem",
                  background: "#1f2937",
                  marginBottom: "1rem",
                  animation: "otcShimmer 2s linear infinite",
                }}
              />
              <div
                aria-hidden="true"
                style={{
                  width: "100%",
                  height: "2.25rem",
                  borderRadius: "0.5rem",
                  background: "linear-gradient(90deg, #1f2937, #374151, #1f2937)",
                  backgroundSize: "200% 100%",
                  marginBottom: "1rem",
                  animation: "otcShimmer 2s linear infinite",
                }}
              />
              <div
                aria-hidden="true"
                style={{
                  width: "75%",
                  height: "0.75rem",
                  borderRadius: "0.3rem",
                  background: "#111827",
                  animation: "otcShimmer 2s linear infinite",
                }}
              />
            </div>
          ))}
        </div>
      </div>

      <noscript aria-hidden="true">
        <style>{`
          @keyframes otcShimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
          }
          @keyframes otcPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(0.94); }
          }
        `}</style>
      </noscript>
    </div>
  );
}
