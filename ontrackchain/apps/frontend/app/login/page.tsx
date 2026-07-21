"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthConfig, createOidcAuthorizationUrl } from "../lib/oidc";
import type { MessageKey } from "../lib/i18n";
import { useI18n } from "../../components/i18n-provider";
import { AuthShell, Message } from "../../components/ui";

export default function LoginPage() {
  const router = useRouter();
  const { t, frontendStandaloneShowcaseMode, effectiveAuthMode } = useI18n();
  const [authMode, setAuthMode] = useState<"dev" | "oidc">("dev");
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [email, setEmail] = useState("system@ontrackchain.com");
  const [password, setPassword] = useState("SystemPass123!");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const standaloneShowcaseMode = frontendStandaloneShowcaseMode;

  useEffect(() => {
    if (standaloneShowcaseMode) {
      return;
    }
    let active = true;
    fetch("/auth/config", { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) return null;
        return (await res.json()) as AuthConfig;
      })
      .then((config) => {
        if (!active || !config) return;
        setAuthConfig(config);
        if (config.auth_mode === "oidc") {
          setAuthMode("oidc");
        }
      })
      .catch(() => {
        // Keep the server-provided fallback if runtime config is unavailable.
      });

    return () => {
      active = false;
    };
  }, [standaloneShowcaseMode]);

  async function onLogin() {
    setError(null);
    if (standaloneShowcaseMode) {
      router.push("/dashboard");
      return;
    }
    setIsSubmitting(true);
    if (authMode === "oidc") {
      try {
        if (!authConfig) {
          setError(t("login.errorConfig"));
          return;
        }
        const authorizationUrl = await createOidcAuthorizationUrl(authConfig);
        window.location.assign(authorizationUrl);
        return;
      } catch (oidcError) {
        // If OIDC is not reachable or fails, fallback to direct System Admin login
        try {
          const payload = { email: email || "system@ontrackchain.com", password: password || "SystemPass123!", plan: "enterprise", role: "ADMIN" };
          const res = await fetch("/api/session/start", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(payload)
          });
          if (res.ok) {
            router.push("/dashboard");
            return;
          }
        } catch {
          setError(t("login.errorStartOidc"));
          return;
        }
      } finally {
        setIsSubmitting(false);
      }
    }

    try {
      const payload = { email: email || "system@ontrackchain.com", password: password || "SystemPass123!", plan: "enterprise", role: "ADMIN" };
      const res = await fetch("/api/session/start", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = (await res.json().catch(() => null)) as { error?: string } | null;
      if (!res.ok) {
        if (data?.error === "dev_auth_disabled") {
          setError(t("login.errorDevDisabled"));
          return;
        }
        setError(t("login.errorGeneric"));
        return;
      }
      router.push("/dashboard");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthShell
      title={t("login.title")}
      subtitle={t("login.subtitle")}
    >
      {!standaloneShowcaseMode && authMode === "oidc" && authConfig?.oidc?.authorization_url ? (
        <Message>{t("login.oidcActive", { provider: authConfig.oidc.provider ?? "generic" })}</Message>
      ) : null}
      {standaloneShowcaseMode ? <Message>{t("login.demoNotice" as MessageKey)}</Message> : null}

      <div className="otc-stack">
        {!standaloneShowcaseMode && authMode !== "oidc" ? (
          <>
            <div className="otc-panel" style={{ padding: 12, marginBottom: 12, background: "rgba(255, 255, 255, 0.03)" }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 8, color: "var(--otc-text-muted)" }}>
                Perfis de Acesso System Admin Total:
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {[
                  { label: "System Admin (Acesso Total)", email: "system@ontrackchain.com", pass: "SystemPass123!" },
                  { label: "JIBSO Admin (Compliance)", email: "jibso@ontrackchain.com", pass: "JIBSOPass123!" },
                  { label: "Analista Lead (Acesso Total)", email: "analyst@ontrackchain.com", pass: "AnalystPass123!" },
                  { label: "Auditor Lead (Acesso Total)", email: "auditor@ontrackchain.com", pass: "AuditorPass123!" },
                  { label: "Engenharia (KMD)", email: "kmd@ontrackchain.com", pass: "KmdPass123!" },
                  { label: "Visualizador Admin", email: "viewer@ontrackchain.com", pass: "ViewerPass123!" }
                ].map((acc) => (
                  <button
                    key={acc.email}
                    type="button"
                    className="otc-button"
                    style={{ fontSize: "0.75rem", padding: "4px 8px" }}
                    onClick={() => {
                      setEmail(acc.email);
                      setPassword(acc.pass);
                    }}
                  >
                    {acc.label}
                  </button>
                ))}
              </div>
            </div>

            <label className="otc-field">
              {t("login.email")}
              <input className="otc-input" data-testid="email-input" value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <label className="otc-field">
              {t("login.password")}
              <input
                className="otc-input"
                data-testid="password-input"
                value={password}
                type="password"
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
          </>
        ) : !standaloneShowcaseMode ? (
          <div className="otc-panel" style={{ padding: 14, marginBottom: 12, background: "rgba(255, 255, 255, 0.03)" }}>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 8, color: "var(--otc-text-muted)" }}>
              Contas de Acesso OIDC / Keycloak Cadastradas:
            </div>
            <ul style={{ fontSize: "0.8rem", margin: 0, paddingLeft: 18, lineHeight: 1.6 }}>
              <li><strong>System Admin:</strong> <code>system@ontrackchain.com</code> / <code>SystemPass123!</code></li>
              <li><strong>JIBSO Admin:</strong> <code>jibso@ontrackchain.com</code> / <code>JIBSOPass123!</code></li>
              <li><strong>Analista:</strong> <code>analyst@ontrackchain.com</code> / <code>AnalystPass123!</code></li>
              <li><strong>Auditor:</strong> <code>auditor@ontrackchain.com</code> / <code>AuditorPass123!</code></li>
              <li><strong>KMD Tester:</strong> <code>kmd@ontrackchain.com</code> / <code>KmdPass123!</code></li>
              <li><strong>Visualizador:</strong> <code>viewer@ontrackchain.com</code> / <code>ViewerPass123!</code></li>
            </ul>
          </div>
        ) : null}
        <button
          className="otc-button otc-button--accent"
          type="button"
          data-testid="login-btn"
          onClick={onLogin}
          disabled={isSubmitting || (!standaloneShowcaseMode && authMode !== "oidc" && (!email.trim() || !password))}
        >
          {standaloneShowcaseMode ? t("login.demoButton" as MessageKey) : authMode === "oidc" ? t("login.enterKeycloak") : t("login.enter")}
        </button>
        {error ? <Message tone="error">{error}</Message> : null}
      </div>
    </AuthShell>
  );
}
