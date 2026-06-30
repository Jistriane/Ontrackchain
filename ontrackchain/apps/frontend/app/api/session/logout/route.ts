import { cookies } from "next/headers";

export async function POST() {
  cookies().set("otc_token", "", { httpOnly: true, expires: new Date(0), path: "/" });
  cookies().set("otc_2fa", "", { httpOnly: true, expires: new Date(0), path: "/" });
  return new Response(JSON.stringify({ status: "ok" }), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}

