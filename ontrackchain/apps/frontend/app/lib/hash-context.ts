export type HashContextSource = "package" | "dossier" | "file";

export type ResolvedHashContext = {
  primaryHash: string;
  source: HashContextSource;
};

export function resolveHashContext(input: {
  packageSha256?: string | null;
  dossierSha256?: string | null;
  fileSha256?: string | null;
}): ResolvedHashContext | null {
  const packageSha256 = input.packageSha256?.trim() ?? "";
  if (packageSha256) {
    return { primaryHash: packageSha256, source: "package" };
  }

  const dossierSha256 = input.dossierSha256?.trim() ?? "";
  if (dossierSha256) {
    return { primaryHash: dossierSha256, source: "dossier" };
  }

  const fileSha256 = input.fileSha256?.trim() ?? "";
  if (fileSha256) {
    return { primaryHash: fileSha256, source: "file" };
  }

  return null;
}
