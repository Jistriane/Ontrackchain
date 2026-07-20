import { cookies } from "next/headers";

export async function POST() {
  cookies().set("otc_2fa", "ok", { httpOnly: true, sameSite: "lax", path: "/" });
  return new Response(JSON.stringify({ status: "ok" }), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
