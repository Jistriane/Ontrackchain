"use client";

import { useEffect } from "react";

export default function CasesError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[Cases Error Boundary]", error?.message, error?.digest);
  }, [error]);

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        padding: "1.5rem",
        margin: "1.5rem",
        borderRadius: "0.75rem",
        border: "1px solid #f59e0b",
        background: "rgba(120, 53, 15, 0.25)",
        color: "#fed7aa",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h2 style={{ margin: 0, marginBottom: "0.5rem", color: "#fdba74" }}>
        Falha no módulo de Gestão de Casos
      </h2>
      <p style={{ margin: 0, marginBottom: "1rem", lineHeight: 1.5 }}>
        A listagem de casos, detalhes ou operações CRUD deste segmento estão
        indisponíveis no momento. Casos já registrados não foram perdidos.
      </p>
      <button
        type="button"
        onClick={() => reset()}
        aria-label="Tentar recarregar a área de gestão de casos"
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
        Recarregar casos
      </button>
    </div>
  );
}
