"use client";

export type OperationalContext = {
  caseId: string;
  requestId: string;
  reportId: string;
  fileHash: string;
  resourceType: string;
  resourceId: string;
  address: string;
  chain: string;
  counterpartyId: string;
  legalName: string;
  documentNumber: string;
  rosId: string;
  reportType: string;
  blockId: string;
};

type AlertOperationalEntry = {
  id: string;
  labels?: Record<string, unknown>;
  annotations?: Record<string, unknown>;
};

type LogOperationalEntry = {
  resource_type: string;
  resource_id: string | null;
  request_id: string | null;
  report_id: string | null;
  file_hash_sha256: string | null;
  metadata: Record<string, unknown>;
};

type ResourceHrefOptions = {
  fallbackResourceType: string;
  preferCaseResource?: boolean;
};

type EvidenceHrefOptions = ResourceHrefOptions & {
  domain?: string;
};

type InvestigateHrefOptions = {
  includeCaseId?: boolean;
};

function emptyOperationalContext(): OperationalContext {
  return {
    caseId: "",
    requestId: "",
    reportId: "",
    fileHash: "",
    resourceType: "",
    resourceId: "",
    address: "",
    chain: "ethereum",
    counterpartyId: "",
    legalName: "",
    documentNumber: "",
    rosId: "",
    reportType: "",
    blockId: ""
  };
}

export function readStringValue(source: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

export function normalizeChain(value: string) {
  return value.trim() || "ethereum";
}

function resolveResourceTarget(context: OperationalContext, options: ResourceHrefOptions) {
  const preferCaseResource = options.preferCaseResource ?? false;
  const resourceType = preferCaseResource && context.caseId ? "case" : context.resourceType || options.fallbackResourceType;
  const resourceId = preferCaseResource && context.caseId
    ? context.caseId
    : context.resourceId || context.reportId || context.requestId || context.caseId;

  return { resourceType, resourceId };
}

export function inferAlertOperationalContext(entry: AlertOperationalEntry): OperationalContext {
  const labels = entry.labels ?? {};
  const annotations = entry.annotations ?? {};
  const caseId =
    readStringValue(labels, ["case_id", "request_id"]) ||
    readStringValue(annotations, ["case_id", "request_id"]);
  const requestId =
    readStringValue(labels, ["request_id", "case_id"]) ||
    readStringValue(annotations, ["request_id", "case_id"]);
  const reportId =
    readStringValue(labels, ["report_id"]) ||
    readStringValue(annotations, ["report_id"]);
  const resourceId =
    readStringValue(labels, ["resource_id", "fingerprint"]) ||
    readStringValue(annotations, ["resource_id"]) ||
    entry.id;
  const address =
    readStringValue(labels, ["address", "target_address", "wallet_address"]) ||
    readStringValue(annotations, ["address", "target_address", "wallet_address"]);
  const chain = normalizeChain(
    readStringValue(labels, ["chain", "target_chain", "blockchain"]) ||
      readStringValue(annotations, ["chain", "target_chain", "blockchain"])
  );

  return {
    ...emptyOperationalContext(),
    caseId,
    requestId,
    reportId,
    resourceType: "operational_alert",
    resourceId,
    address,
    chain
  };
}

export function inferLogOperationalContext(entry: LogOperationalEntry): OperationalContext {
  const metadata = entry.metadata ?? {};
  const resourceType = entry.resource_type.trim();
  const resourceId = (entry.resource_id ?? "").trim() || readStringValue(metadata, ["resource_id"]);

  return {
    ...emptyOperationalContext(),
    caseId: readStringValue(metadata, ["case_id"]),
    requestId: (entry.request_id ?? "").trim() || readStringValue(metadata, ["request_id", "case_id"]),
    reportId: (entry.report_id ?? "").trim() || readStringValue(metadata, ["report_id"]),
    fileHash: (entry.file_hash_sha256 ?? "").trim() || readStringValue(metadata, ["file_hash_sha256", "evidence_hash"]),
    resourceType,
    resourceId,
    address: readStringValue(metadata, ["address", "target_address", "wallet_address"]),
    chain: normalizeChain(readStringValue(metadata, ["chain", "target_chain", "wallet_chain"])),
    counterpartyId: (resourceType === "counterparty" ? resourceId : "") || readStringValue(metadata, ["counterparty_id"]),
    legalName: readStringValue(metadata, ["legal_name"]),
    documentNumber: readStringValue(metadata, ["document_number"]),
    rosId: (resourceType === "ros_record" ? resourceId : "") || readStringValue(metadata, ["ros_id"]),
    reportType: readStringValue(metadata, ["report_type"]),
    blockId: (resourceType === "preventive_block" ? resourceId : "") || readStringValue(metadata, ["block_id"])
  };
}

export function buildCaseHref(caseId: string) {
  const normalized = caseId.trim();
  return normalized ? `/cases/${encodeURIComponent(normalized)}` : null;
}

export function buildAuditHref(context: OperationalContext, options: ResourceHrefOptions) {
  const target = resolveResourceTarget(context, options);
  const params = new URLSearchParams({
    resource_type: target.resourceType,
    resource_id: target.resourceId
  });
  if (context.requestId) {
    params.set("request_id", context.requestId);
  }
  if (context.reportId) {
    params.set("report_id", context.reportId);
  }
  return `/audit?${params.toString()}`;
}

export function buildEvidenceHref(context: OperationalContext, options: EvidenceHrefOptions) {
  const target = resolveResourceTarget(context, options);
  const params = new URLSearchParams({
    domain: options.domain ?? "all",
    resource_type: target.resourceType,
    resource_id: target.resourceId
  });
  if (context.requestId) {
    params.set("request_id", context.requestId);
  }
  if (context.reportId) {
    params.set("report_id", context.reportId);
  }
  return `/evidence?${params.toString()}`;
}

export function buildReportsHref(context: OperationalContext) {
  const params = new URLSearchParams();
  if (context.caseId) {
    params.set("case_id", context.caseId);
  }
  if (context.reportType) {
    params.set("report_type", context.reportType);
  }
  return `/reports${params.toString() ? `?${params.toString()}` : ""}`;
}

export function buildInvestigateHref(context: OperationalContext, options: InvestigateHrefOptions = {}) {
  if (!context.address) {
    return null;
  }
  const params = new URLSearchParams({
    address: context.address,
    chain: context.chain,
    report_type: "technical_basic"
  });
  if (options.includeCaseId && context.caseId) {
    params.set("case_id", context.caseId);
  }
  return `/investigate?${params.toString()}`;
}

export function buildSanctionsHref(context: OperationalContext) {
  if (!context.address) {
    return null;
  }
  const params = new URLSearchParams({
    address: context.address,
    chain: context.chain,
    autostart: "1"
  });
  if (context.caseId) {
    params.set("case_id", context.caseId);
  }
  return `/sanctions?${params.toString()}`;
}

export function buildBlocksHref(context: OperationalContext) {
  if (!context.address) {
    return null;
  }
  const params = new URLSearchParams({
    address: context.address,
    chain: context.chain,
    autostart: "1"
  });
  if (context.caseId) {
    params.set("case_id", context.caseId);
  }
  return `/blocks?${params.toString()}`;
}

export function buildCounterpartyHref(context: OperationalContext) {
  if (!context.counterpartyId && !context.legalName && !context.documentNumber) {
    return null;
  }
  const params = new URLSearchParams();
  if (context.counterpartyId) {
    params.set("counterparty_id", context.counterpartyId);
  }
  if (context.legalName) {
    params.set("legal_name", context.legalName);
  }
  if (context.documentNumber) {
    params.set("document_number", context.documentNumber);
  }
  return `/counterparties?${params.toString()}`;
}

export function buildRosHref(context: OperationalContext) {
  if (!context.rosId && !context.caseId) {
    return null;
  }
  const params = new URLSearchParams();
  if (context.rosId) {
    params.set("ros_id", context.rosId);
  }
  if (context.caseId) {
    params.set("case_id", context.caseId);
  }
  return `/ros-coaf?${params.toString()}`;
}
