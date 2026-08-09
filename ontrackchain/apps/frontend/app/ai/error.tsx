"use client";

import { useEffect } from "react";

export default function AiError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[AI Intelligence Error Boundary]", error?.message, error?.digest);
  }, [error]);

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        padding: "1.5rem",
        margin: "1.5rem",
        borderRadius: "0.75rem",
        border: "1px solid #a855f7",
        background: "rgba(88, 28, 135, 0.25)",
        color: "#e9d5ff",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h2 style={{ margin: 0, marginBottom: "0.5rem", color: "#d8b4fe" }}>
        Módulo de AI Intelligence indisponível
      </h2>
      <p style={{ margin: 0, marginBottom: "1rem", lineHeight: 1.5 }}>
        Explicação de decisões, análise de grafo ou geração de insights
        falharam temporariamente. As solicitações já enviadas estão na fila de
        reprocessamento do time de engenharia.
      </p>
      <button
        type="button"
        onClick={() => reset()}
        aria-label="Tentar recarregar as funcionalidades de AI"
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
        Recarregar AI Intelligence
      </button>
    </div>
  );
}
