import Link from "next/link";
import React from "react";

export default function NotFound() {
  return (
    <main
      role="main"
      aria-labelledby="not-found-title"
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        fontFamily: "system-ui, sans-serif",
        background:
          "linear-gradient(180deg, #0b1220 0%, #0f172a 100%)",
        color: "#e5e7eb",
      }}
    >
      <div
        style={{
          maxWidth: "36rem",
          width: "100%",
          textAlign: "center",
          padding: "2.5rem",
          borderRadius: "1rem",
          border: "1px solid #1f2937",
          background: "rgba(17, 24, 39, 0.9)",
        }}
      >
        <div
          aria-hidden="true"
          style={{
            fontSize: "4rem",
            fontWeight: 800,
            background:
              "linear-gradient(135deg, #818cf8 0%, #f97316 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            marginBottom: "0.5rem",
          }}
        >
          404
        </div>
        <h1
          id="not-found-title"
          style={{
            fontSize: "1.5rem",
            fontWeight: 700,
            marginBottom: "1rem",
          }}
        >
          A rota que você procura não existe
        </h1>
        <p
          style={{
            lineHeight: 1.55,
            color: "#9ca3af",
            marginBottom: "2rem",
          }}
        >
          Esta página pode ter sido movida, renomeada ou você seguiu um link
          desatualizado. Confira o endereço digitado ou volte para a navegação
          principal.
        </p>
        <nav aria-label="Navegação de erro 404" style={{ display: "flex", gap: "0.75rem", justifyContent: "center", flexWrap: "wrap" }}>
          <Link
            href="/dashboard"
            aria-label="Ir para o Dashboard da Ontrackchain"
            style={{
              padding: "0.7rem 1.25rem",
              borderRadius: "0.5rem",
              background: "#6366f1",
              color: "white",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            Ir para o Dashboard
          </Link>
          <Link
            href="/login"
            aria-label="Retornar para a página de autenticação"
            style={{
              padding: "0.7rem 1.25rem",
              borderRadius: "0.5rem",
              border: "1px solid #334155",
              background: "transparent",
              color: "#e5e7eb",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            Voltar ao Login
          </Link>
        </nav>
      </div>
    </main>
  );
}
