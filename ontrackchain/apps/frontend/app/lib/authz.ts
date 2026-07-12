export function normalizeAuthRole(role: string | null | undefined) {
  return String(role ?? "").trim().toUpperCase();
}

export function canReadBilling(role: string | null | undefined) {
  const normalizedRole = normalizeAuthRole(role);
  return normalizedRole === "ADMIN" || normalizedRole === "BILLING_ADMIN" || normalizedRole === "OTK_BILLING_ADMIN";
}
