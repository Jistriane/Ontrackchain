export type AuthContext = {
  org_id: string | null;
  user_id: string | null;
  linked_user_id: string | null;
  role: string | null;
  plan: string | null;
  auth_method: string | null;
  mfa_mode: string | null;
  mfa_provider_homologated: string | null;
  two_factor: string | null;
};

type ResolveOwnerUserIdInput = {
  ownerLabel?: string | null;
  linkedUserId?: string | null;
  existingOwnerUserId?: string | null;
  isUuidLike: (value: string | null | undefined) => boolean;
};

export async function fetchAuthContext(): Promise<AuthContext | null> {
  const res = await fetch("/api/app/auth/context", { cache: "no-store" });
  if (!res.ok) {
    return null;
  }

  return (await res.json().catch(() => null)) as AuthContext | null;
}

export function resolveOwnerUserId({
  ownerLabel,
  linkedUserId,
  existingOwnerUserId,
  isUuidLike
}: ResolveOwnerUserIdInput): string | null {
  const ownerFromExisting = isUuidLike(existingOwnerUserId) ? existingOwnerUserId?.trim() ?? null : null;
  const ownerFromLabel = isUuidLike(ownerLabel) ? ownerLabel?.trim() ?? null : null;
  const ownerFromSession = isUuidLike(linkedUserId) ? linkedUserId?.trim() ?? null : null;
  return ownerFromExisting || ownerFromLabel || ownerFromSession;
}
