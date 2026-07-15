"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthConfig, createOidcAuthorizationUrl } from "../lib/oidc";
import type { MessageKey } from "../lib/i18n";
import { useI18n } from "../../components/i18n-provider";
import { AuthShell, Message } from "../../components/ui";

export default function LoginPage() {
  const router = useRouter();
  const { t, frontendStandaloneDemoMode } = useI18n();
  const [authMode, setAuthMode] = useState<"dev" | "oidc">(process.env.NEXT_PUBLIC_AUTH_MODE === "oidc" ? "oidc" : "dev");
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [require2fa, setRequire2fa] = useState(false);
  const [totp, setTotp] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const standaloneDemoMode = frontendStandaloneDemoMode;

  useEffect(() => {
    if (standaloneDemoMode) {
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
        setAuthMode(config.effective_auth_mode ?? config.auth_mode);
      })
      .catch(() => {
        // Keep the build-time fallback if runtime config is unavailable.
      });

    return () => {
      active = false;
    };
  }, [standaloneDemoMode]);

  async function onLogin() {
    setError(null);
    if (standaloneDemoMode) {
      setError(t("login.demoUnavailable" as MessageKey));
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
        if (oidcError instanceof Error && oidcError.message === "missing_oidc_runtime_config") {
          setError(t("login.errorMissingRuntime"));
          return;
        }
        setError(t("login.errorStartOidc"));
        return;
      } finally {
        setIsSubmitting(false);
      }
    }

    try {
      const payload = { email, password, plan: "professional" };
      const res = await fetch("/api/session/start", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = (await res.json().catch(() => null)) as { require2fa?: boolean; error?: string } | null;
      if (!res.ok) {
        if (data?.error === "dev_auth_disabled") {
          setError(t("login.errorDevDisabled"));
          return;
        }
        setError(t("login.errorGeneric"));
        return;
      }
      if (data?.require2fa) {
        setRequire2fa(true);
        return;
      }
      router.push("/dashboard");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onVerify2fa() {
    setError(null);
    const res = await fetch("/api/session/verify-2fa", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ code: totp })
    });
    const data = (await res.json().catch(() => null)) as { error?: string } | null;
    if (!res.ok) {
      if (data?.error === "invalid_2fa") {
        setError(t("login.errorInvalid2fa"));
        return;
      }
      if (data?.error === "oidc_2fa_managed_externally") {
        setError(t("login.errorOidc2faExternal"));
        return;
      }
      if (data?.error === "not_authenticated") {
        setError(t("login.errorNotAuthenticated"));
        return;
      }
      setError(t("login.error2faGeneric"));
      return;
    }
    router.push("/dashboard");
  }

  return (
    <AuthShell
      title={t("login.title")}
      subtitle={t("login.subtitle")}
    >
      {authMode === "oidc" && authConfig?.oidc?.authorization_url ? (
        <Message>{t("login.oidcActive", { provider: authConfig.oidc.provider ?? "generic" })}</Message>
      ) : null}
      {authMode === "oidc" ? (
        <Message>{t("login.oidc2fa")}</Message>
      ) : null}
      {authConfig?.auth_mode === "dev" && authConfig.dev_auth_enabled === false ? (
        <Message tone="error">
          {t("login.devBlocked", { appEnv: authConfig.app_env ?? "unknown" })}
        </Message>
      ) : null}
      {standaloneDemoMode ? <Message>{t("login.demoNotice" as MessageKey)}</Message> : null}

      <div className="otc-stack">
        {authMode !== "oidc" ? (
          <>
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
        ) : (
          <Message>{t("login.devRedirectReplaced")}</Message>
        )}
        <button
          className="otc-button otc-button--accent"
          type="button"
          data-testid="login-btn"
          onClick={onLogin}
          disabled={standaloneDemoMode || isSubmitting || (authMode !== "oidc" && (!email.trim() || !password))}
        >
          {standaloneDemoMode ? t("login.demoButton" as MessageKey) : authMode === "oidc" ? t("login.enterKeycloak") : t("login.enter")}
        </button>
        {error ? <Message tone="error">{error}</Message> : null}
      </div>

      {require2fa && authMode !== "oidc" ? (
        <section data-testid="2fa-modal" className="otc-panel">
          <div className="otc-section__header">
            <div>
              <h2 className="otc-section__title">{t("login.secondFactor.title")}</h2>
              <p className="otc-section__description">
                {t("login.secondFactor.description", {
                  issuer: authConfig?.mfa?.issuer ? ` (${authConfig.mfa.issuer})` : ""
                })}
              </p>
            </div>
          </div>
          <label className="otc-field">
            {t("login.secondFactor.code")}
            <input className="otc-input" data-testid="totp-input" value={totp} onChange={(e) => setTotp(e.target.value)} />
          </label>
          <button className="otc-button" type="button" data-testid="verify-2fa-btn" onClick={onVerify2fa} style={{ marginTop: 12 }}>
            {t("login.secondFactor.verify")}
          </button>
        </section>
      ) : null}
    </AuthShell>
  );
}
