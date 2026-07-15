import type { ReactNode } from "react";
import type { Metadata } from "next";
import { cookies } from "next/headers";
import "./globals.css";
import { I18nProvider } from "../components/i18n-provider";
import { isFrontendStandaloneDemoMode } from "./lib/auth-runtime";
import { LOCALE_COOKIE_NAME, normalizeLocale } from "./lib/i18n";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? process.env.NEXT_PUBLIC_FRONTEND_URL ?? "http://localhost:8080";

export const metadata: Metadata = {
  metadataBase: new URL(APP_URL),
  title: "OnTrackChain",
  description: "Compliance driven by on-chain intelligence.",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: "/icon.png",
    other: [{ rel: "icon", url: "/favicon.ico" }],
    shortcut: "/icon.png",
    apple: "/apple-icon.png"
  },
  openGraph: {
    title: "OnTrackChain",
    description: "Compliance driven by on-chain intelligence.",
    type: "website",
    siteName: "OnTrackChain",
    images: [
      {
        url: "/branding/ontrackchain-social-card.png",
        width: 1200,
        height: 630,
        alt: "OnTrackChain social preview"
      }
    ]
  },
  twitter: {
    card: "summary_large_image",
    title: "OnTrackChain",
    description: "Compliance driven by on-chain intelligence.",
    images: ["/branding/ontrackchain-social-card.png"]
  }
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const locale = normalizeLocale(cookies().get(LOCALE_COOKIE_NAME)?.value);
  const frontendStandaloneDemoMode = isFrontendStandaloneDemoMode();

  return (
    <html lang={locale} suppressHydrationWarning>
      <body suppressHydrationWarning>
        <I18nProvider initialLocale={locale} frontendStandaloneDemoMode={frontendStandaloneDemoMode}>
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
