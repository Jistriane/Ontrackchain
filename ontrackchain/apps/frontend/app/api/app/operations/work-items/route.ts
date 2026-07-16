import {
  isFrontendStandaloneShowcaseMode,
} from "../../../../lib/auth-runtime";
import {
  listStandaloneShowcaseWorkItems,
  upsertStandaloneShowcaseWorkItem
} from "../../../../lib/standalone-showcase";
import type {
  BlocksWorkItemMetadata,
  CreateWorkItemRequest,
  CounterpartyWorkItemMetadata,
  EvidenceWorkItemMetadata,
  ReportWorkItemMetadata,
  RosCoafWorkItemMetadata,
  SanctionsWorkItemMetadata
} from "../../../../lib/work-items";
import { authenticateRequest, proxyOperationsRequest } from "../_shared";

const EMPTY_WORK_ITEMS = {
  data: [],
  page: 1,
  limit: 100,
  total: 0,
  has_more: false
} as const;

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const url = new URL(request.url);
    return new Response(
      JSON.stringify(
        listStandaloneShowcaseWorkItems({
          module: url.searchParams.get("module"),
          resourceType: url.searchParams.get("resource_type"),
          reportExternalId: url.searchParams.get("report_external_id"),
          limit: Number(url.searchParams.get("limit") ?? 100)
        })
      ),
      {
        status: 200,
        headers: { "content-type": "application/json" }
      }
    );
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return new Response(JSON.stringify(EMPTY_WORK_ITEMS), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  return proxyOperationsRequest(auth, {
    method: "GET",
    path: `/api/v1/operations/work-items${query}`,
    requestId
  });
}

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as
      | CreateWorkItemRequest<ReportWorkItemMetadata>
      | CreateWorkItemRequest<CounterpartyWorkItemMetadata>
      | CreateWorkItemRequest<SanctionsWorkItemMetadata>
      | CreateWorkItemRequest<BlocksWorkItemMetadata>
      | CreateWorkItemRequest<RosCoafWorkItemMetadata>
      | CreateWorkItemRequest<EvidenceWorkItemMetadata>
      | null;
    if (!payload?.resource_id) {
      return new Response(JSON.stringify({ error: "invalid_work_item_payload" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    const isReportPayload = payload.resource_type === "formal_report_case" && payload.module === "reports";
    const isCounterpartyPayload = payload.resource_type === "counterparty" && payload.module === "counterparties";
    const isSanctionsPayload = payload.resource_type === "sanctions_screening" && payload.module === "sanctions";
    const isBlocksPayload = payload.resource_type === "preventive_block" && payload.module === "blocks";
    const isRosPayload = payload.resource_type === "ros_record" && payload.module === "ros_coaf";
    const isEvidencePayload = payload.resource_type === "evidence_event" && payload.module === "evidence";
    if (
      !isReportPayload &&
      !isCounterpartyPayload &&
      !isSanctionsPayload &&
      !isBlocksPayload &&
      !isRosPayload &&
      !isEvidencePayload
    ) {
      return new Response(JSON.stringify({ error: "unsupported_work_item_payload" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    const normalizedPayload = isReportPayload
      ? ({
          ...payload,
          module: "reports",
          resource_type: "formal_report_case"
        } as CreateWorkItemRequest<ReportWorkItemMetadata>)
      : isCounterpartyPayload
        ? ({
          ...payload,
          module: "counterparties",
          resource_type: "counterparty"
        } as CreateWorkItemRequest<CounterpartyWorkItemMetadata>)
        : isSanctionsPayload
          ? ({
            ...payload,
            module: "sanctions",
            resource_type: "sanctions_screening"
          } as CreateWorkItemRequest<SanctionsWorkItemMetadata>)
          : isBlocksPayload
            ? ({
              ...payload,
              module: "blocks",
              resource_type: "preventive_block"
            } as CreateWorkItemRequest<BlocksWorkItemMetadata>)
            : isRosPayload
              ? ({
                  ...payload,
                  module: "ros_coaf",
                  resource_type: "ros_record"
                } as CreateWorkItemRequest<RosCoafWorkItemMetadata>)
              : ({
                  ...payload,
                  module: "evidence",
                  resource_type: "evidence_event"
                } as CreateWorkItemRequest<EvidenceWorkItemMetadata>);
    return new Response(
      JSON.stringify(
        upsertStandaloneShowcaseWorkItem(normalizedPayload)
      ),
      {
      status: 200,
      headers: { "content-type": "application/json" }
      }
    );
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  return proxyOperationsRequest(auth, {
    method: "POST",
    path: "/api/v1/operations/work-items",
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
