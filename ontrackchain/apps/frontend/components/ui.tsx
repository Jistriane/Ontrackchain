"use client";

import type { ReactNode } from "react";
import Image from "next/image";
import type { Locale, MessageKey } from "../app/lib/i18n";
import { useI18n } from "./i18n-provider";

type NavItem = {
  href: string;
  label: MessageKey;
};

type AppShellProps = {
  title: string;
  subtitle: string;
  activePath?: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
};

type PanelProps = {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

type MetricCardProps = {
  label: string;
  value: ReactNode;
  meta?: ReactNode;
  accent?: boolean;
};

type ModuleCardProps = {
  title: string;
  description: string;
  footer?: ReactNode;
  badge?: ReactNode;
  href?: string;
};

const NAV_ITEMS: NavItem[] = [
  { href: "/investigate", label: "nav.investigate" },
  { href: "/monitoring", label: "nav.monitoring" },
  { href: "/audit", label: "nav.audit" },
  { href: "/dashboard", label: "nav.dashboard" },
  { href: "/billing", label: "nav.billing" }
];

function joinClasses(...parts: Array<string | undefined>) {
  return parts.filter(Boolean).join(" ");
}

function BrandLogo({ className, priority = false }: { className?: string; priority?: boolean }) {
  return (
    <div className={joinClasses("otc-brand__logo-frame", className)}>
      <Image
        src="/branding/ontrackchain-wordmark.png"
        alt="OnTrackChain"
        fill
        priority={priority}
        sizes="(max-width: 768px) 132px, 160px"
        className="otc-brand__logo"
      />
    </div>
  );
}

function BrandBadge({ className, priority = false }: { className?: string; priority?: boolean }) {
  return (
    <div className={joinClasses("otc-brand__badge-frame", className)}>
      <Image
        src="/branding/ontrackchain-badge-192.png"
        alt="OnTrackChain badge"
        fill
        priority={priority}
        sizes="(max-width: 768px) 38px, 44px"
        className="otc-brand__badge"
      />
    </div>
  );
}

function BrandLockup({
  priority = false,
  badgeClassName,
  logoClassName
}: {
  priority?: boolean;
  badgeClassName?: string;
  logoClassName?: string;
}) {
  return (
    <div className="otc-brand__lockup">
      <BrandBadge className={badgeClassName} priority={priority} />
      <BrandLogo className={logoClassName} priority={priority} />
    </div>
  );
}

export function AppShell({ title, subtitle, activePath, eyebrow, actions, children }: AppShellProps) {
  const { locale, setLocale, t, locales } = useI18n();
  const resolvedEyebrow = eyebrow ?? t("app.eyebrow");

  return (
    <div className="otc-shell">
      <div className="otc-shell__inner">
        <header className="otc-topbar">
          <div className="otc-brand">
            <a href="/" className="otc-brand__home-link" aria-label="OnTrackChain">
              <BrandLockup priority />
            </a>
            <p className="otc-brand__eyebrow">{resolvedEyebrow}</p>
          </div>
          <nav className="otc-nav" aria-label={t("nav.aria")}>
            {NAV_ITEMS.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className={joinClasses("otc-nav__link", activePath === item.href ? "otc-nav__link--active" : undefined)}
              >
                {t(item.label)}
              </a>
            ))}
          </nav>
          <div className="otc-topbar__meta">
            <label className="otc-locale">
              <span className="otc-locale__label">{t("locale.label")}</span>
              <select className="otc-select otc-locale__select" value={locale} onChange={(event) => setLocale(event.target.value as Locale)}>
                {locales.map((item) => (
                  <option key={item} value={item}>
                    {t(`locale.${item}` as MessageKey)}
                  </option>
                ))}
              </select>
            </label>
            <span className="otc-status-pill">{t("topbar.online")}</span>
            <span className="otc-ghost-pill">{t("topbar.systemUser")}</span>
            <a href="/login" className="otc-nav__link">
              {t("topbar.logout")}
            </a>
          </div>
        </header>

        <main className="otc-page otc-theme">
          <section className="otc-hero otc-panel">
            <div>
              <p className="otc-hero__eyebrow">{resolvedEyebrow}</p>
              <h1 className="otc-hero__title">{title}</h1>
              <p className="otc-hero__subtitle">{subtitle}</p>
            </div>
            {actions ? <div className="otc-actions">{actions}</div> : null}
          </section>
          {children}
        </main>
      </div>
    </div>
  );
}

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  const { locale, setLocale, t, locales } = useI18n();

  return (
    <div className="otc-auth">
      <div className="otc-panel otc-auth__card">
        <div className="otc-auth__header">
          <div className="otc-auth__brand-block">
            <a href="/" className="otc-brand__home-link" aria-label="OnTrackChain">
              <BrandLockup badgeClassName="otc-brand__badge-frame--auth" logoClassName="otc-brand__logo-frame--auth" priority />
            </a>
            <p className="otc-hero__eyebrow otc-auth__eyebrow">{t("auth.eyebrow")}</p>
          </div>
          <label className="otc-locale">
            <span className="otc-locale__label">{t("locale.label")}</span>
            <select className="otc-select otc-locale__select" value={locale} onChange={(event) => setLocale(event.target.value as Locale)}>
              {locales.map((item) => (
                <option key={item} value={item}>
                  {t(`locale.${item}` as MessageKey)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <h1 className="otc-auth__title">{title}</h1>
        <p className="otc-auth__subtitle">{subtitle}</p>
        <div className="otc-stack otc-auth__content">
          {children}
        </div>
      </div>
    </div>
  );
}

export function Panel({ title, description, actions, children, className }: PanelProps) {
  return (
    <section className={joinClasses("otc-panel", className)}>
      {title || description || actions ? (
        <div className="otc-section__header">
          <div>
            {title ? <h2 className="otc-section__title">{title}</h2> : null}
            {description ? <p className="otc-section__description">{description}</p> : null}
          </div>
          {actions}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export function MetricGrid({ children }: { children: ReactNode }) {
  return <section className="otc-stat-grid">{children}</section>;
}

export function MetricCard({ label, value, meta, accent = false }: MetricCardProps) {
  return (
    <div className="otc-stat">
      <p className="otc-stat__label">{label}</p>
      <div className={joinClasses("otc-stat__value", accent ? "otc-stat__value--accent" : undefined)}>{value}</div>
      {meta ? <p className="otc-stat__meta">{meta}</p> : null}
    </div>
  );
}

export function ModuleGrid({ children }: { children: ReactNode }) {
  return <div className="otc-module-grid">{children}</div>;
}

export function ModuleCard({ title, description, footer, badge, href }: ModuleCardProps) {
  const content = (
    <div className="otc-card otc-module-card">
      <div className="otc-module-card__title">
        <strong>{title}</strong>
        {badge}
      </div>
      <p className="otc-module-card__description">{description}</p>
      {footer ? <div className="otc-module-card__footer">{footer}</div> : null}
    </div>
  );

  if (!href) {
    return content;
  }

  return <a href={href}>{content}</a>;
}

export function CodeBlock({ children }: { children: ReactNode }) {
  return <pre className="otc-code">{children}</pre>;
}

export function Message({
  children,
  tone = "default"
}: {
  children: ReactNode;
  tone?: "default" | "error" | "success";
}) {
  return <div className={joinClasses("otc-message", tone === "error" ? "otc-message--error" : undefined, tone === "success" ? "otc-message--success" : undefined)}>{children}</div>;
}

export function Pill({ children, tone = "success" }: { children: ReactNode; tone?: "success" | "warning" | "danger" }) {
  return <span className={joinClasses("otc-pill", tone === "warning" ? "otc-pill--warning" : undefined, tone === "danger" ? "otc-pill--danger" : undefined)}>{children}</span>;
}
