"use client";

import { startTransition, useEffect, useEffectEvent, useRef, useState } from "react";

type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

type LogEvent = {
  id: string;
  timestamp: string;
  level: LogLevel;
  service: string;
  source: string;
  environment: string;
  message: string;
  exception?: string;
  job_id?: string;
  video_id?: string;
  request_id?: string;
};

type LogHistoryResponse = {
  logs: LogEvent[];
};

const MAX_VISIBLE_LOGS = 500;
const levelOptions: Array<LogLevel | "ALL"> = [
  "ALL",
  "DEBUG",
  "INFO",
  "WARNING",
  "ERROR",
  "CRITICAL",
];
const serviceOptions = [
  "ALL",
  "backend",
  "frontend",
  "video_maker",
  "text_overlay",
  "ai_worker",
  "post_worker",
  "voice_cloner",
  "sound_designer",
];

const formatTimestamp = (timestamp: string) => {
  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) return timestamp;
  return parsed.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

const formatService = (service: string) =>
  service
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const parseResponse = async (response: Response) => {
  try {
    return (await response.json()) as LogHistoryResponse & { detail?: string };
  } catch {
    return null;
  }
};

const mergeLogs = (previous: LogEvent[], incoming: LogEvent[]) => {
  const events = new Map(previous.map((event) => [event.id, event]));
  incoming.forEach((event) => events.set(event.id, event));
  return [...events.values()]
    .sort((first, second) => second.id.localeCompare(first.id, undefined, { numeric: true }))
    .slice(0, MAX_VISIBLE_LOGS);
};

const levelClassName = (level: LogLevel) => {
  if (level === "ERROR" || level === "CRITICAL") return "text-status-error";
  if (level === "WARNING") return "text-status-warning";
  if (level === "INFO") return "text-status-success";
  return "text-soft";
};

export default function WorkerControlPanel() {
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [levelFilter, setLevelFilter] = useState<LogLevel | "ALL">("ALL");
  const [serviceFilter, setServiceFilter] = useState("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState("Connecting");
  const [error, setError] = useState<string | null>(null);
  const lastEventId = useRef<string | null>(null);

  const appendEvents = useEffectEvent((incoming: LogEvent[]) => {
    if (incoming.length === 0) return;
    lastEventId.current = incoming.at(-1)?.id ?? lastEventId.current;
    startTransition(() => {
      setLogs((previous) => mergeLogs(previous, incoming));
    });
  });

  const loadHistory = useEffectEvent(async (signal: AbortSignal) => {
    try {
      const response = await fetch("/api/logs?limit=100", {
        cache: "no-store",
        signal,
      });
      const payload = await parseResponse(response);
      if (!response.ok || !payload || !Array.isArray(payload.logs)) {
        throw new Error(payload?.detail ?? "Unable to load application logs.");
      }
      appendEvents(payload.logs);
      setError(null);
    } catch (fetchError) {
      if (fetchError instanceof DOMException && fetchError.name === "AbortError") return;
      setError(
        fetchError instanceof Error
          ? fetchError.message
          : "Unable to load application logs."
      );
    } finally {
      setIsLoading(false);
    }
  });

  useEffect(() => {
    const controller = new AbortController();
    let eventSource: EventSource | null = null;

    const connect = async () => {
      await loadHistory(controller.signal);
      if (controller.signal.aborted) return;

      const streamUrl = new URL("/api/logs/stream", window.location.origin);
      if (lastEventId.current) {
        streamUrl.searchParams.set("last_event_id", lastEventId.current);
      }
      eventSource = new EventSource(streamUrl);
      eventSource.addEventListener("open", () => setStreamStatus("Live"));
      eventSource.addEventListener("log", (message) => {
        try {
          appendEvents([JSON.parse(message.data) as LogEvent]);
        } catch {
          setError("Received an invalid log event.");
        }
      });
      eventSource.addEventListener("error", () => setStreamStatus("Reconnecting"));
    };

    void connect();

    return () => {
      controller.abort();
      eventSource?.close();
    };
  }, []);

  const filteredLogs = logs.filter(
    (event) =>
      (levelFilter === "ALL" || event.level === levelFilter) &&
      (serviceFilter === "ALL" || event.service === serviceFilter)
  );

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <section className="neon-panel rounded-3xl p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-soft">
              Operations
            </p>
            <h1 className="font-display text-3xl font-semibold sm:text-4xl">
              Application Logs
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-muted sm:text-base">
              Recent backend and worker events, updated in real time from Redis Streams.
            </p>
          </div>
          <span className={`neon-pill ${streamStatus === "Live" ? "" : "opacity-70"}`}>
            {streamStatus}
          </span>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-semibold text-high">
            Level
            <select
              className="surface-subtle mt-2 w-full rounded-xl border border-[var(--stroke-soft)] px-3 py-2 text-sm text-high"
              onChange={(event) => setLevelFilter(event.target.value as LogLevel | "ALL")}
              value={levelFilter}
            >
              {levelOptions.map((level) => (
                <option key={level} value={level}>
                  {level === "ALL" ? "All levels" : level}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-semibold text-high">
            Service
            <select
              className="surface-subtle mt-2 w-full rounded-xl border border-[var(--stroke-soft)] px-3 py-2 text-sm text-high"
              onChange={(event) => setServiceFilter(event.target.value)}
              value={serviceFilter}
            >
              {serviceOptions.map((service) => (
                <option key={service} value={service}>
                  {service === "ALL" ? "All services" : formatService(service)}
                </option>
              ))}
            </select>
          </label>
        </div>

        {error ? <p className="alert alert-error mt-5">{error}</p> : null}
      </section>

      <section className="neon-card overflow-hidden rounded-3xl">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--stroke-soft)] px-6 py-4 sm:px-7">
          <h2 className="font-display text-2xl font-semibold">Events</h2>
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-soft">
            {filteredLogs.length} shown
          </span>
        </div>

        {isLoading ? (
          <p className="p-6 text-sm text-muted sm:p-7">Loading application logs...</p>
        ) : filteredLogs.length === 0 ? (
          <p className="p-6 text-sm text-soft sm:p-7">No matching log events yet.</p>
        ) : (
          <div className="divide-y divide-[var(--stroke-soft)]">
            {filteredLogs.map((event) => (
              <article className="px-6 py-4 sm:px-7" key={event.id}>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold uppercase tracking-[0.14em]">
                  <span className="text-soft">{formatTimestamp(event.timestamp)}</span>
                  <span className={levelClassName(event.level)}>{event.level}</span>
                  <span className="text-muted">{formatService(event.service)}</span>
                  {event.video_id ? <span className="text-soft">Video {event.video_id}</span> : null}
                  {event.job_id ? <span className="text-soft">Job {event.job_id}</span> : null}
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm text-high">{event.message}</p>
                {event.exception ? (
                  <details className="surface-subtle mt-3 rounded-xl p-3 text-xs text-status-error">
                    <summary className="cursor-pointer font-semibold">Show exception details</summary>
                    <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap font-mono text-xs">
                      {event.exception}
                    </pre>
                  </details>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
