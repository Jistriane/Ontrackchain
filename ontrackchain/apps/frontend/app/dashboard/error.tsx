"use client";

import { useEffect } from "react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[Dashboard Error Boundary]", error?.message, error?.digest);
  }, [error]);

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        padding: "1.5rem",
        margin: "1.5rem",
        borderRadius: "0.75rem",
        border: "1px solid #f87171",
        background: "rgba(127, 29, 29, 0.25)",
        color: "#fecaca",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h2 style={{ margin: 0, marginBottom: "0.5rem", color: "#fca5a5" }}>
        Não foi possível carregar o Dashboard
      </h2>
      <p style={{ margin: 0, marginBottom: "1rem", lineHeight: 1.5 }}>
        Falha ao consultar KPIs e métricas da área principal. Tente novamente
        em instantes; se o problema persistir, contate o time de SRE.
      </p>
      <button
        type="button"
        onClick={() => reset()}
        aria-label="Tentar carregar o dashboard novamente"
        style={{
          padding: "0.6rem 1.1rem",
          borderRadius: "0.5rem",
          background: "#6366f1",
          border: "none",
          color: "white",
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        Tentar novamente
      </button>
    </div>
  );
}
