"use client";

import { useEffect } from "react";

export default function EvidenceError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[Evidence Package Error Boundary]", error?.message, error?.digest);
  }, [error]);

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        padding: "1.5rem",
        margin: "1.5rem",
        borderRadius: "0.75rem",
        border: "1px solid #10b981",
        background: "rgba(6, 78, 59, 0.25)",
        color: "#a7f3d0",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h2 style={{ margin: 0, marginBottom: "0.5rem", color: "#6ee7b7" }}>
        Pacote de Evidências não pode ser exibido
      </h2>
      <p style={{ margin: 0, marginBottom: "1rem", lineHeight: 1.5 }}>
        O lacre criptográfico SHA-256 dos arquivos segue válido e a integridade
        está preservada — houve apenas falha na renderização da tela. Baixe o
        PDF diretamente pela API B2B se necessário.
      </p>
      <button
        type="button"
        onClick={() => reset()}
        aria-label="Tentar carregar novamente a área de evidências"
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
        Recarregar Evidências
      </button>
    </div>
  );
}
