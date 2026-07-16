"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "../../../components/i18n-provider";
import { AuthShell, Message } from "../../../components/ui";

import {
  clearRememberedOidcCallbackMessage,
  consumeOidcLoginState,
  readRememberedOidcCallbackMessage,
  rememberOidcCallbackMessage
} from "../../lib/oidc";

function OidcCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t, frontendStandaloneShowcaseMode } = useI18n();
  const [message, setMessage] = useState(t("oidc.message.completing"));
  const hasAttemptedLoginRef = useRef(false);

  useEffect(() => {
    if (hasAttemptedLoginRef.current) {
      return;
    }
    hasAttemptedLoginRef.current = true;

    let active = true;

    async function completeLogin() {
      if (frontendStandaloneShowcaseMode) {
        if (active) {
          setMessage(t("login.demoNotice"));
        }
        router.replace("/dashboard");
        return;
      }

      const rememberedMessage = readRememberedOidcCallbackMessage();
      const code = searchParams.get("code");
      const returnedState = searchParams.get("state");
      const providerError = searchParams.get("error");
      const providerErrorDescription = searchParams.get("error_description");

      function finishWithMessage(nextMessage: string) {
        rememberOidcCallbackMessage(nextMessage);
        if (!active) {
          return;
        }
        setMessage(nextMessage);
      }

      if (providerError) {
        finishWithMessage(providerErrorDescription || t("oidc.message.providerDenied"));
        return;
      }

      const storedState = consumeOidcLoginState();
      if (!code || !returnedState || !storedState) {
        if (rememberedMessage && code && returnedState) {
          if (!active) {
            return;
          }
          setMessage(rememberedMessage);
          return;
        }
        finishWithMessage(t("oidc.message.stateMissing"));
        return;
      }

      if (storedState.state !== returnedState) {
        finishWithMessage(t("oidc.message.stateMismatch"));
        return;
      }

      const res = await fetch("/api/session/start", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          code,
          codeVerifier: storedState.codeVerifier,
          redirectUri: storedState.redirectUri
        })
      });

      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { error?: string } | null;
        if (data?.error === "missing_oidc_code_exchange") {
          finishWithMessage(t("oidc.message.exchangeFailed"));
          return;
        }
        if (data?.error === "invalid_claims") {
          finishWithMessage(t("oidc.message.invalidClaims"));
          return;
        }
        finishWithMessage(t("oidc.message.sessionFailed"));
        return;
      }

      clearRememberedOidcCallbackMessage();
      router.replace("/dashboard");
    }

    void completeLogin();

    return () => {
      active = false;
    };
  }, [frontendStandaloneShowcaseMode, router, searchParams, t]);

  return (
    <AuthShell
      title={t("oidc.title")}
      subtitle={t("oidc.subtitle")}
    >
      <Message>{message}</Message>
      <Message>{t("oidc.returnToLogin")}</Message>
    </AuthShell>
  );
}

export default function OidcCallbackPage() {
  return (
    <Suspense
      fallback={<CallbackFallback />}
    >
      <OidcCallbackContent />
    </Suspense>
  );
}

function CallbackFallback() {
  const { t } = useI18n();

  return (
    <AuthShell title={t("oidc.title")} subtitle={t("oidc.fallbackSubtitle")}>
      <Message>{t("oidc.loading")}</Message>
    </AuthShell>
  );
}
