export function ensureHttpUrl(raw: string | undefined | null, fallback: string): string {
  const value = (raw ?? "").trim();
  if (!value) {
    return fallback;
  }
  if (value.startsWith("http://") || value.startsWith("https://")) {
    return value;
  }
  return `http://${value}`;
}
