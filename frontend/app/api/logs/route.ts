import { createBackendLogUrl, getLogApiKey } from "@/log-api";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const logApiKey = getLogApiKey();
  if (!logApiKey) {
    return Response.json(
      { detail: "Log service is not configured." },
      { status: 503 }
    );
  }

  try {
    const upstream = await fetch(
      createBackendLogUrl("/api/logs", new URL(request.url).search),
      {
        cache: "no-store",
        headers: { "X-Log-API-Key": logApiKey },
      }
    );

    return new Response(upstream.body, {
      headers: { "Content-Type": upstream.headers.get("Content-Type") ?? "application/json" },
      status: upstream.status,
    });
  } catch {
    return Response.json(
      { detail: "Unable to reach the log service." },
      { status: 502 }
    );
  }
}
