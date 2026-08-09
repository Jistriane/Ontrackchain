"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[Ontrackchain Global Error Boundary]", {
      message: error?.message,
      stack: error?.stack,
      digest: error?.digest,
      isoTimestamp: new Date().toISOString(),
    });
  }, [error]);

  return (
    <html lang="pt-BR">
      <body>
        <main
          role="main"
          aria-labelledby="global-error-title"
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "2rem",
            fontFamily: "system-ui, sans-serif",
            background:
              "linear-gradient(180deg, #0b1220 0%, #111a2e 100%)",
            color: "#f3f4f6",
          }}
        >
          <div
            style={{
              maxWidth: "36rem",
              width: "100%",
              padding: "2rem",
              borderRadius: "0.75rem",
              border: "1px solid #1f2937",
              background: "rgba(17, 24, 39, 0.85)",
              boxShadow: "0 10px 40px rgba(0,0,0,0.45)",
            }}
          >
            <div
              role="img"
              aria-label="Aviso de erro do sistema"
              style={{
                fontSize: "2.5rem",
                marginBottom: "1rem",
                display: "block",
              }}
            >
              🚨
            </div>
            <h1
              id="global-error-title"
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                marginBottom: "0.5rem",
                color: "#f87171",
              }}
            >
              Instabilidade detectada no sistema
            </h1>
            <p
              style={{
                lineHeight: 1.55,
                color: "#d1d5db",
                marginBottom: "1.25rem",
              }}
            >
              Uma falha inesperada aconteceu durante o carregamento da plataforma
              Ontrackchain. Este incidente foi registrado no log central para
              análise do time de SRE.
            </p>
            <div
              role="note"
              aria-live="polite"
              style={{
                padding: "0.75rem 1rem",
                borderRadius: "0.5rem",
                background: "rgba(30, 41, 59, 0.65)",
                border: "1px solid #334155",
                marginBottom: "1.5rem",
              }}
            >
              <strong style={{ color: "#e5e7eb" }}>ID do erro:&nbsp;</strong>
              <code
                style={{
                  fontSize: "0.875rem",
                  background: "#0b1220",
                  padding: "0.15rem 0.4rem",
                  borderRadius: "0.25rem",
                  color: "#a5b4fc",
                }}
              >
                {error?.digest ?? error?.name ?? "ERROR-UNKNOWN"}
              </code>
            </div>
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              <button
                type="button"
                onClick={() => reset()}
                aria-label="Tentar carregar a tela novamente"
                style={{
                  padding: "0.7rem 1.25rem",
                  borderRadius: "0.5rem",
                  border: "none",
                  background: "#6366f1",
                  color: "white",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Tentar novamente
              </button>
              <a
                href="/dashboard"
                aria-label="Voltar para o painel principal"
                style={{
                  padding: "0.7rem 1.25rem",
                  borderRadius: "0.5rem",
                  border: "1px solid #334155",
                  background: "transparent",
                  color: "#e5e7eb",
                  textDecoration: "none",
                  fontWeight: 600,
                }}
              >
                Ir para o Dashboard
              </a>
              <a
                href="/login"
                aria-label="Retornar para a tela de login"
                style={{
                  padding: "0.7rem 1.25rem",
                  borderRadius: "0.5rem",
                  border: "1px solid #1f2937",
                  background: "transparent",
                  color: "#cbd5e1",
                  textDecoration: "none",
                  fontWeight: 500,
                }}
              >
                Fazer login novamente
              </a>
            </div>
          </div>
        </main>
      </body>
    </html>
  );
}
