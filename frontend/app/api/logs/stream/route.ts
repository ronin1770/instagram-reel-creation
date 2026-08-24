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
    const lastEventId = request.headers.get("Last-Event-ID");
    const upstream = await fetch(
      createBackendLogUrl("/api/logs/stream", new URL(request.url).search),
      {
        cache: "no-store",
        headers: {
          "X-Log-API-Key": logApiKey,
          ...(lastEventId ? { "Last-Event-ID": lastEventId } : {}),
        },
      }
    );

    return new Response(upstream.body, {
      headers: {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "Content-Type": upstream.headers.get("Content-Type") ?? "text/event-stream",
        "X-Accel-Buffering": "no",
      },
      status: upstream.status,
    });
  } catch {
    return Response.json(
      { detail: "Unable to reach the log stream." },
      { status: 502 }
    );
  }
}
