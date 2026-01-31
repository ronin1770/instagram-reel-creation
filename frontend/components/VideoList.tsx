"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

type VideoRecord = {
  video_id: string;
  video_title: string;
  video_size?: number | string | null;
  video_introduction?: string | null;
  creation_time?: string;
  modification_time?: string;
  active?: boolean;
  video_tags?: string[];
  status?: string;
  output_file_location?: string | null;
  job_id?: string | null;
  error_reason?: string | null;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const formatDateTime = (value?: string) => {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

const normalizeStatus = (status?: string) =>
  (status ?? "created").toLowerCase();

const statusLabel = (status?: string) => {
  const normalized = normalizeStatus(status);
  if (normalized === "queued") return "Queued";
  if (normalized === "processing") return "Processing";
  if (normalized === "completed") return "Completed";
  if (normalized === "failed") return "Failed";
  if (normalized === "created") return "Created";
  return normalized.replace(/\b\w/g, (char) => char.toUpperCase());
};

const statusClass = (status?: string) => {
  const normalized = normalizeStatus(status);
  if (normalized === "completed") return "text-emerald-200";
  if (normalized === "failed") return "text-rose-200";
  if (normalized === "processing") return "text-sky-200";
  if (normalized === "queued") return "text-indigo-200";
  if (normalized === "created") return "text-amber-200";
  return "text-soft";
};

const StatusPill = ({ status }: { status?: string }) => (
  <span
    className={`neon-badge text-[10px] font-semibold uppercase tracking-[0.25em] ${statusClass(
      status
    )}`}
  >
    {statusLabel(status)}
  </span>
);

const sortByRecent = (items: VideoRecord[]) =>
  [...items].sort((a, b) => {
    const aTime = new Date(a.modification_time ?? a.creation_time ?? 0).getTime();
    const bTime = new Date(b.modification_time ?? b.creation_time ?? 0).getTime();
    return bTime - aTime;
  });

export default function VideoList() {
  const [videos, setVideos] = useState<VideoRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchVideos = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/videos`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Unable to load videos (${response.status})`);
      }
      const data = (await response.json()) as VideoRecord[];
      setVideos(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load videos.");
    } finally {
      setIsLoading(false);
    }
  }, [API_BASE]);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  const grouped = useMemo(() => {
    const created: VideoRecord[] = [];
    const failed: VideoRecord[] = [];
    const attempted: VideoRecord[] = [];

    sortByRecent(videos).forEach((video) => {
      const normalized = normalizeStatus(video.status);
      if (normalized === "failed") {
        failed.push(video);
      } else if (normalized === "created") {
        created.push(video);
      } else {
        attempted.push(video);
      }
    });

    return { created, failed, attempted };
  }, [videos]);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
      <section className="neon-panel rounded-3xl p-6 md:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <span className="neon-pill">Video vault</span>
            <h1 className="font-display text-3xl font-semibold sm:text-4xl">
              Recent reels
            </h1>
            <p className="text-muted">
              Monitor everything you created, failed runs, and all attempted
              renders in one place.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <span className="neon-chip">{videos.length} total</span>
            <span className="neon-chip">{grouped.created.length} created</span>
            <span className="neon-chip">{grouped.attempted.length} attempted</span>
            <span className="neon-chip">{grouped.failed.length} failed</span>
          </div>
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            className="neon-button neon-button-ghost"
            type="button"
            onClick={fetchVideos}
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh"}
          </button>
          <Link className="neon-button neon-button-primary" href="/create_video">
            Create Video
          </Link>
        </div>
        {error && (
          <div className="mt-4 rounded-2xl border border-rose-400/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        )}
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="neon-panel rounded-3xl p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-soft">
                Created
              </p>
              <p className="text-xs text-muted">
                Fresh videos waiting to be processed.
              </p>
            </div>
            <span className="neon-chip">{grouped.created.length}</span>
          </div>
          <div className="mt-4 space-y-3">
            {grouped.created.length === 0 && (
              <p className="text-sm text-soft">
                {isLoading ? "Loading videos..." : "No created videos yet."}
              </p>
            )}
            {grouped.created.map((video) => (
              <article
                key={video.video_id}
                className="neon-card rounded-2xl p-4 text-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-base font-semibold">
                      {video.video_title || "Untitled video"}
                    </p>
                    <p className="text-xs text-soft">ID: {video.video_id}</p>
                  </div>
                  <StatusPill status={video.status} />
                </div>
                {video.video_introduction && (
                  <p className="mt-2 text-xs text-muted">
                    {video.video_introduction}
                  </p>
                )}
                <p className="mt-3 text-xs text-soft">
                  Updated {formatDateTime(video.modification_time)}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="neon-panel rounded-3xl p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-soft">
                Attempted
              </p>
              <p className="text-xs text-muted">
                Queued, processing, or completed runs.
              </p>
            </div>
            <span className="neon-chip">{grouped.attempted.length}</span>
          </div>
          <div className="mt-4 space-y-3">
            {grouped.attempted.length === 0 && (
              <p className="text-sm text-soft">
                {isLoading ? "Loading videos..." : "No attempted videos yet."}
              </p>
            )}
            {grouped.attempted.map((video) => (
              <article
                key={video.video_id}
                className="neon-card rounded-2xl p-4 text-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-base font-semibold">
                      {video.video_title || "Untitled video"}
                    </p>
                    <p className="text-xs text-soft">ID: {video.video_id}</p>
                  </div>
                  <StatusPill status={video.status} />
                </div>
                {video.video_introduction && (
                  <p className="mt-2 text-xs text-muted">
                    {video.video_introduction}
                  </p>
                )}
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted">
                  {video.video_size && (
                    <span className="neon-chip">
                      Size: {String(video.video_size)}
                    </span>
                  )}
                  {video.output_file_location && (
                    <span
                      className="neon-chip max-w-[220px] truncate"
                      title={video.output_file_location}
                    >
                      Output: {video.output_file_location}
                    </span>
                  )}
                </div>
                <p className="mt-2 text-xs text-soft">
                  Updated {formatDateTime(video.modification_time)}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="neon-panel rounded-3xl p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-soft">
                Failed
              </p>
              <p className="text-xs text-muted">
                Runs that need attention or a retry.
              </p>
            </div>
            <span className="neon-chip">{grouped.failed.length}</span>
          </div>
          <div className="mt-4 space-y-3">
            {grouped.failed.length === 0 && (
              <p className="text-sm text-soft">
                {isLoading ? "Loading videos..." : "No failures yet."}
              </p>
            )}
            {grouped.failed.map((video) => (
              <article
                key={video.video_id}
                className="neon-card rounded-2xl p-4 text-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-base font-semibold">
                      {video.video_title || "Untitled video"}
                    </p>
                    <p className="text-xs text-soft">ID: {video.video_id}</p>
                  </div>
                  <StatusPill status={video.status} />
                </div>
                {video.error_reason && (
                  <p className="mt-2 text-xs text-rose-200">
                    Error: {video.error_reason}
                  </p>
                )}
                <p className="mt-3 text-xs text-soft">
                  Updated {formatDateTime(video.modification_time)}
                </p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
