import type { Locale } from "./i18n";

export const INTL_LOCALE_BY_APP_LOCALE: Record<Locale, string> = {
  "pt-BR": "pt-BR",
  en: "en-US",
  es: "es-ES"
};

export function formatDateTime(value: string | null | undefined, locale: Locale) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(INTL_LOCALE_BY_APP_LOCALE[locale], {
    dateStyle: "short",
    timeStyle: "short"
  }).format(parsed);
}
