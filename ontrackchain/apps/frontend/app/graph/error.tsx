"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function GraphIntelligenceError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    try {
      console.error("[Graph Intelligence 4.0] Segmento /app/graph/error boundary ativado:", error);
    } catch {}
  }, [error]);

  return (
    <html lang="pt-BR">
      <body>
        <main
          role="main"
          aria-labelledby="graph-error-title"
          className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-amber-50 to-orange-50 p-6"
          data-testid="graph-error-boundary"
        >
          <section className="max-w-2xl w-full bg-white border border-red-200 rounded-2xl shadow-lg p-8">
            <header>
              <h1 id="graph-error-title" data-testid="graph-error-title" className="text-2xl font-bold text-red-800">
                Ops — Módulo Graph Intelligence 4.0 indisponível temporariamente
              </h1>
              <p className="text-slate-600 mt-2">
                Ocorreu um erro durante a renderização do grafo interativo de inteligência de contrapartes.
                Tente recarregar o módulo. Se o problema persistir, contate a equipe de suporte.
              </p>
            </header>
            <dl className="mt-5 text-sm bg-red-50 border border-red-100 rounded-lg p-4 space-y-2">
              <div className="flex gap-3">
                <dt className="font-semibold text-red-800 min-w-[140px]">Mensagem:</dt>
                <dd className="text-slate-700 break-words">{error?.message ?? "Erro não especificado"}</dd>
              </div>
              <div className="flex gap-3">
                <dt className="font-semibold text-red-800 min-w-[140px]">Digest:</dt>
                <dd className="font-mono text-xs text-slate-600 break-all">
                  {error?.digest ?? "N/A (Next.js não gerou digest)"}
                </dd>
              </div>
              <div className="flex gap-3">
                <dt className="font-semibold text-red-800 min-w-[140px]">Módulo:</dt>
                <dd className="text-slate-700">app/graph/* (Graph Intelligence 4.0 T2-05)</dd>
              </div>
            </dl>
            <div className="mt-7 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => reset()}
                data-testid="graph-error-reset"
                aria-label="Tentar recarregar o módulo Graph Intelligence"
                className="inline-flex items-center px-5 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-red-400"
              >
                🔄 Tentar novamente
              </button>
              <Link
                href="/dashboard"
                data-testid="graph-error-back-dashboard"
                aria-label="Voltar para o painel principal"
                className="inline-flex items-center px-5 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold border border-slate-200 transition-colors"
              >
                ← Voltar Dashboard
              </Link>
              <Link
                href="/cases"
                data-testid="graph-error-cases"
                aria-label="Abrir lista de casos investigativos"
                className="inline-flex items-center px-5 py-2.5 rounded-lg text-slate-700 font-semibold border border-slate-300 hover:bg-slate-50 transition-colors"
              >
                📁 Lista de casos
              </Link>
            </div>
          </section>
        </main>
      </body>
    </html>
  );
}
