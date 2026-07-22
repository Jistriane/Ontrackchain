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

  async function onDirectLogin() {
    setError(null);
    if (standaloneShowcaseMode) {
      router.push("/dashboard");
      return;
    }
    setIsSubmitting(true);
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

  async function onOidcLogin() {
    setError(null);
    setIsSubmitting(true);
    try {
      if (!authConfig) {
        setError(t("login.errorConfig"));
        return;
      }
      const authorizationUrl = await createOidcAuthorizationUrl(authConfig);
      window.location.assign(authorizationUrl);
    } catch (oidcError) {
      // Fallback a System Admin direto
      try {
        const payload = { email: "system@ontrackchain.com", password: "SystemPass123!", plan: "enterprise", role: "ADMIN" };
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
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthShell
      title={t("login.title")}
      subtitle={t("login.subtitle")}
    >
      {standaloneShowcaseMode ? <Message>{t("login.demoNotice" as MessageKey)}</Message> : null}

      <div className="otc-stack">
        {!standaloneShowcaseMode ? (
          <>
            <div className="otc-panel" style={{ padding: 12, marginBottom: 4, background: "rgba(255, 255, 255, 0.03)" }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 8, color: "var(--otc-text-soft)" }}>
                Atalhos de Acesso Rápido (System Admin):
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

            <button
              className="otc-button otc-button--accent"
              type="button"
              data-testid="login-btn"
              onClick={onDirectLogin}
              disabled={isSubmitting || (!email.trim() || !password)}
            >
              {t("login.enter")}
            </button>
          </>
        ) : (
          <button
            className="otc-button otc-button--accent"
            type="button"
            data-testid="login-btn"
            onClick={onDirectLogin}
            disabled={isSubmitting}
          >
            {t("login.demoButton" as MessageKey)}
          </button>
        )}

        {!standaloneShowcaseMode && authMode === "oidc" ? (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: 10, margin: "10px 0" }}>
              <div style={{ flex: 1, height: 1, background: "var(--otc-border)" }} />
              <span style={{ fontSize: "0.75rem", color: "var(--otc-text-faint)", textTransform: "uppercase", letterSpacing: "0.1em" }}>OU</span>
              <div style={{ flex: 1, height: 1, background: "var(--otc-border)" }} />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {authConfig?.oidc?.authorization_url ? (
                <Message>{t("login.oidcActive", { provider: authConfig.oidc.provider ?? "generic" })}</Message>
              ) : null}

              <button
                className="otc-button"
                type="button"
                style={{ background: "rgba(255, 255, 255, 0.08)", border: "1px solid var(--otc-border)" }}
                onClick={onOidcLogin}
                disabled={isSubmitting}
              >
                {t("login.enterKeycloak")}
              </button>
            </div>
          </>
        ) : null}

        {error ? <Message tone="error">{error}</Message> : null}
      </div>
    </AuthShell>
  );
}

