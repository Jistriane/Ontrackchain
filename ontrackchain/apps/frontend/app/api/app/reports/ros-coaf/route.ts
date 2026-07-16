import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import {
  generateStandaloneShowcaseRosCoaf,
  listStandaloneShowcaseRosCoaf
} from "../../../../lib/standalone-showcase";
import { authenticateReportRequest, jsonResponse, proxyReportJsonRequest } from "../_shared";

const EMPTY_ROS_COAF_LIST_RESPONSE = {
  data: [],
  page: 1,
  limit: 100,
  total: 0,
  has_more: false
} as const;

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const url = new URL(request.url);
    return jsonResponse(
      JSON.stringify(
        listStandaloneShowcaseRosCoaf({
          page: Number(url.searchParams.get("page") ?? 1),
          limit: Number(url.searchParams.get("limit") ?? 100),
          reportId: url.searchParams.get("report_id"),
          rosId: url.searchParams.get("ros_id")
        })
      ),
      200
    );
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return jsonResponse(JSON.stringify(EMPTY_ROS_COAF_LIST_RESPONSE), 200);
  }

  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  const response = await proxyReportJsonRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/ros-coaf${query}`,
    requestId
  });
  if (response.status === 401 || response.status === 403) {
    return jsonResponse(JSON.stringify(EMPTY_ROS_COAF_LIST_RESPONSE), 200);
  }
  return response;
}

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const body = (await request.json().catch(() => null)) as { ros_id?: string | null } | null;
    if (!body?.ros_id?.trim()) {
      return jsonResponse(JSON.stringify({ error: "missing_ros_id" }), 422);
    }
    return jsonResponse(
      JSON.stringify(generateStandaloneShowcaseRosCoaf({ rosId: body.ros_id })),
      200
    );
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  return proxyReportJsonRequest(auth, {
    method: "POST",
    path: "/api/v1/reports/ros-coaf",
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
