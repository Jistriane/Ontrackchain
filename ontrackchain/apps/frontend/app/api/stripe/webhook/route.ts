import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const signature = request.headers.get("stripe-signature");
    const bodyText = await request.text();

    if (!signature) {
      return NextResponse.json({ error: "Missing stripe-signature header" }, { status: 400 });
    }

    // Processamento simulado/integrado de evento Stripe Webhook
    let event: { type?: string; data?: { object?: Record<string, unknown> } } = {};
    try {
      event = JSON.parse(bodyText);
    } catch {
      return NextResponse.json({ error: "Invalid JSON payload" }, { status: 400 });
    }

    const eventType = event.type ?? "checkout.session.completed";

    if (eventType === "checkout.session.completed") {
      const session = event.data?.object ?? {};
      const orgId = String(session.org_id ?? "default_org");
      const credits = Number(session.credits_allocated ?? 5000);

      return NextResponse.json({
        status: "success",
        processed: true,
        event_type: eventType,
        org_id: orgId,
        credits_added: credits,
        timestamp: new Date().toISOString(),
      });
    }

    return NextResponse.json({ status: "ignored", event_type: eventType });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal error processing Stripe webhook";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
