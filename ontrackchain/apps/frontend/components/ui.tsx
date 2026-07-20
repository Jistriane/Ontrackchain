"use client";

import { useEffect, useId, useMemo, useState, type HTMLAttributes, type ReactNode } from "react";
import Image from "next/image";
import {
  canManageFederatedIdentity,
  canReadBilling,
  canReadCounterparty,
  canReadInvestigationAdmin,
  canReadMonitoringAdmin
} from "../app/lib/authz";
import type { Locale, MessageKey } from "../app/lib/i18n";
import { fetchAuthContext } from "../app/lib/ownership";
import { useI18n } from "./i18n-provider";

type NavItem = {
  href: string;
  label: MessageKey;
  icon: ReactNode;
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
  testId?: string;
};

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description: ReactNode;
  confirmLabel: string;
  cancelLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
  tone?: "default" | "danger";
  testId?: string;
};

function NavIcon({ children }: { children: ReactNode }) {
  return (
    <span className="otc-nav__icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        {children}
      </svg>
    </span>
  );
}

const NAV_ITEMS: NavItem[] = [
  {
    href: "/dashboard",
    label: "nav.dashboard",
    icon: (
      <NavIcon>
        <path d="M4 13h7V4H4z" />
        <path d="M13 20h7v-9h-7z" />
        <path d="M13 4h7v5h-7z" />
        <path d="M4 20h7v-5H4z" />
      </NavIcon>
    )
  },
  {
    href: "/investigate",
    label: "nav.investigate",
    icon: (
      <NavIcon>
        <circle cx="11" cy="11" r="6" />
        <path d="m20 20-4.2-4.2" />
      </NavIcon>
    )
  },
  {
    href: "/monitoring",
    label: "nav.monitoring",
    icon: (
      <NavIcon>
        <path d="M4 18h16" />
        <path d="M7 15V9" />
        <path d="M12 15V6" />
        <path d="M17 15v-3" />
      </NavIcon>
    )
  },
  {
    href: "/incident-response",
    label: "nav.incidentResponse" as MessageKey,
    icon: (
      <NavIcon>
        <path d="M12 21s7-4.4 7-10V5l-7-2-7 2v6c0 5.6 7 10 7 10Z" />
        <path d="M12 8v5" />
        <path d="M12 16h.01" />
      </NavIcon>
    )
  },
  {
    href: "/alerts",
    label: "nav.alerts",
    icon: (
      <NavIcon>
        <path d="M12 22a2.5 2.5 0 0 0 2.5-2.5h-5A2.5 2.5 0 0 0 12 22" />
        <path d="M18 16v-5a6 6 0 1 0-12 0v5l-2 2h16z" />
      </NavIcon>
    )
  },
  {
    href: "/audit",
    label: "nav.audit",
    icon: (
      <NavIcon>
        <path d="M12 3 5 6v6c0 4.2 2.7 7.7 7 9 4.3-1.3 7-4.8 7-9V6z" />
        <path d="m9.5 12 1.7 1.7 3.3-3.4" />
      </NavIcon>
    )
  },
  {
    href: "/counterparties",
    label: "nav.counterparties",
    icon: (
      <NavIcon>
        <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="8.5" cy="7" r="3.5" />
        <path d="M20 8v6" />
        <path d="M17 11h6" />
      </NavIcon>
    )
  },
  {
    href: "/sanctions",
    label: "nav.sanctions",
    icon: (
      <NavIcon>
        <path d="M12 3 4 7v5c0 4.5 3 8.2 8 9.8 5-1.6 8-5.3 8-9.8V7z" />
        <path d="M9.5 12.2 11 13.7 14.6 10.1" />
      </NavIcon>
    )
  },
  {
    href: "/blocks",
    label: "nav.blocks",
    icon: (
      <NavIcon>
        <path d="M6 9h12" />
        <path d="M6 15h12" />
        <path d="M10 3h4" />
        <path d="M10 21h4" />
        <path d="M8 7 4 12l4 5" />
        <path d="M16 7 20 12l-4 5" />
      </NavIcon>
    )
  },
  {
    href: "/evidence",
    label: "nav.evidence",
    icon: (
      <NavIcon>
        <path d="M12 3 5 7v5c0 4 2.5 7.4 7 9 4.5-1.6 7-5 7-9V7z" />
        <path d="M10 12h4" />
        <path d="M12 10v4" />
      </NavIcon>
    )
  },
  {
    href: "/ros-coaf",
    label: "nav.rosCoaf",
    icon: (
      <NavIcon>
        <path d="M6 3h12v18H6z" />
        <path d="M9 7h6" />
        <path d="M9 11h6" />
        <path d="M9 15h6" />
      </NavIcon>
    )
  },
  {
    href: "/reports",
    label: "nav.reports",
    icon: (
      <NavIcon>
        <path d="M6 3h12v18H6z" />
        <path d="M9 7h6" />
        <path d="M9 11h6" />
        <path d="M9 15h6" />
        <path d="M8 19h8" />
      </NavIcon>
    )
  },
  {
    href: "/billing",
    label: "nav.billing",
    icon: (
      <NavIcon>
        <path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" />
        <circle cx="9.5" cy="7" r="3.5" />
        <path d="M20 8v6" />
        <path d="M17 11h6" />
      </NavIcon>
    )
  },
  {
    href: "/team",
    label: "nav.team",
    icon: (
      <NavIcon>
        <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="8.5" cy="7" r="3.5" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a3.5 3.5 0 0 1 0 6.75" />
      </NavIcon>
    )
  }
];

const ROLE_GATED_NAV_ITEMS = new Set(["/billing", "/counterparties", "/incident-response", "/alerts", "/team"]);

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
        suppressHydrationWarning
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
        suppressHydrationWarning
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
  const { locale, setLocale, t, locales, frontendStandaloneShowcaseMode } = useI18n();
  const resolvedEyebrow = eyebrow ?? t("app.eyebrow");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [authRole, setAuthRole] = useState<string | null | undefined>(undefined);

  useEffect(() => {
    const stored = window.localStorage.getItem("otc-sidebar-collapsed");
    if (stored === "true") {
      setSidebarCollapsed(true);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("otc-sidebar-collapsed", sidebarCollapsed ? "true" : "false");
  }, [sidebarCollapsed]);

  useEffect(() => {
    let cancelled = false;

    fetchAuthContext()
      .then((context) => {
        if (!cancelled) {
          setAuthRole(context?.role ?? null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAuthRole(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const visibleNavItems = useMemo(
    () =>
      NAV_ITEMS.filter((item) => {
        if (frontendStandaloneShowcaseMode) {
          return true;
        }
        if (authRole === undefined) {
          return !ROLE_GATED_NAV_ITEMS.has(item.href);
        }
        if (item.href === "/billing") {
          return canReadBilling(authRole);
        }
        if (item.href === "/counterparties") {
          return canReadCounterparty(authRole);
        }
        if (item.href === "/alerts") {
          return canReadMonitoringAdmin(authRole);
        }
        if (item.href === "/incident-response") {
          return canReadInvestigationAdmin(authRole) || canReadMonitoringAdmin(authRole);
        }
        if (item.href === "/team") {
          return authRole !== null;
        }
        return true;
      }),
    [authRole, frontendStandaloneShowcaseMode]
  );

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
            {frontendStandaloneShowcaseMode ? (
              <span className="otc-ghost-pill">Showcase</span>
            ) : authRole === null ? (
              <a href="/login" className="otc-button otc-button--accent" style={{ padding: "4px 12px", fontSize: "0.8rem" }}>
                Login
              </a>
            ) : (
              <a href="/login" className="otc-topbar__logout">
                {t("topbar.logout")}
              </a>
            )}
          </div>
        </header>

        <div className={joinClasses("otc-workspace", sidebarCollapsed ? "otc-workspace--collapsed" : undefined)}>
          <aside className={joinClasses("otc-sidebar", "otc-panel", sidebarCollapsed ? "otc-sidebar--collapsed" : undefined)}>
            <div className="otc-sidebar__header">
              <p className="otc-sidebar__eyebrow">{t("nav.aria")}</p>
              <button
                type="button"
                className="otc-button otc-button--ghost otc-sidebar__toggle"
                aria-label={sidebarCollapsed ? "Expandir menu lateral" : "Recolher menu lateral"}
                onClick={() => setSidebarCollapsed((current) => !current)}
                title={sidebarCollapsed ? "Expandir menu lateral" : "Recolher menu lateral"}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  {sidebarCollapsed ? <path d="m9 6 6 6-6 6" /> : <path d="m15 6-6 6 6 6" />}
                </svg>
              </button>
            </div>
            <nav className="otc-nav otc-nav--sidebar" aria-label={t("nav.aria")}>
              {visibleNavItems.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  data-tooltip={sidebarCollapsed ? t(item.label) : undefined}
                  className={joinClasses(
                    "otc-nav__link",
                    "otc-nav__link--sidebar",
                    item.href === "/dashboard" ? "otc-nav__link--primary" : undefined,
                    activePath === item.href ? "otc-nav__link--active" : undefined
                  )}
                >
                  <span className="otc-nav__item">
                    {item.icon}
                    <span className={joinClasses("otc-nav__text", sidebarCollapsed ? "otc-nav__text--hidden" : undefined)}>{t(item.label)}</span>
                  </span>
                </a>
              ))}
            </nav>
            <div className={joinClasses("otc-sidebar__footer", sidebarCollapsed ? "otc-sidebar__footer--collapsed" : undefined)}>
              <span className="otc-status-pill">{t("topbar.online")}</span>
              <span className={joinClasses("otc-ghost-pill", sidebarCollapsed ? "otc-ghost-pill--compact" : undefined)}>
                {frontendStandaloneShowcaseMode ? "Showcase" : t("topbar.systemUser")}
              </span>
            </div>
          </aside>

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

export function ModuleCard({ title, description, footer, badge, href, testId }: ModuleCardProps) {
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

  return (
    <a href={href} data-testid={testId}>
      {content}
    </a>
  );
}

export function CodeBlock({ children }: { children: ReactNode }) {
  return <pre className="otc-code">{children}</pre>;
}

export function Message({
  children,
  tone = "default",
  className,
  ...props
}: {
  children: ReactNode;
  tone?: "default" | "error" | "success";
} & HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={joinClasses(
        "otc-message",
        tone === "error" ? "otc-message--error" : undefined,
        tone === "success" ? "otc-message--success" : undefined,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function Pill({
  children,
  tone = "success",
  ...props
}: { children: ReactNode; tone?: "success" | "warning" | "danger" } & React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={joinClasses("otc-pill", tone === "warning" ? "otc-pill--warning" : undefined, tone === "danger" ? "otc-pill--danger" : undefined)}
      {...props}
    >
      {children}
    </span>
  );
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
  busy = false,
  tone = "default",
  testId
}: ConfirmDialogProps) {
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (!open) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !busy) {
        onCancel();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [busy, onCancel, open]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="otc-dialog-backdrop"
      data-testid={testId}
      onClick={(event) => {
        if (event.target === event.currentTarget && !busy) {
          onCancel();
        }
      }}
    >
      <div className="otc-dialog" role="dialog" aria-modal="true" aria-labelledby={titleId} aria-describedby={descriptionId}>
        <div className="otc-dialog__body">
          <h2 className="otc-dialog__title" id={titleId}>
            {title}
          </h2>
          <div className="otc-dialog__description" id={descriptionId}>
            {description}
          </div>
        </div>
        <div className="otc-dialog__actions">
          <button
            className="otc-button otc-button--ghost"
            type="button"
            onClick={onCancel}
            disabled={busy}
            data-testid={testId ? `${testId}-cancel` : undefined}
          >
            {cancelLabel}
          </button>
          <button
            className={joinClasses("otc-button", tone === "danger" ? "otc-button--danger" : "otc-button--accent")}
            type="button"
            onClick={onConfirm}
            disabled={busy}
            data-testid={testId ? `${testId}-confirm` : undefined}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
