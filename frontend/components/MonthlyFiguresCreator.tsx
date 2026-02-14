"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from "react";

type CallApiSuccess = {
  message: string;
  ai_type: string;
  job_id: string;
  status: string;
};

type RawPostRecord = {
  _id?: string;
  id?: string;
  code?: string;
  name?: string;
  country?: string;
  dob?: string;
  excellence_field?: string;
  added_on?: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const fallback = (value?: string) => value?.trim() || "—";

const formatDate = (value?: string) => {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
  }).format(date);
};

const getErrorMessage = async (response: Response) => {
  try {
    const data = (await response.json()) as { detail?: unknown };
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item) =>
          typeof item === "object" &&
          item !== null &&
          "msg" in item &&
          typeof item.msg === "string"
            ? item.msg
            : ""
        )
        .filter(Boolean)
        .join(", ");
    }
  } catch {
    return null;
  }
  return null;
};

export default function MonthlyFiguresCreator() {
  const [givenMonth, setGivenMonth] = useState("March");
  const [fieldOfExcellence, setFieldOfExcellence] = useState("Movies");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [jobResult, setJobResult] = useState<CallApiSuccess | null>(null);

  const [records, setRecords] = useState<RawPostRecord[]>([]);
  const [isLoadingRecords, setIsLoadingRecords] = useState(true);
  const [recordsError, setRecordsError] = useState<string | null>(null);

  const fetchMonthlyFigures = useCallback(async () => {
    setIsLoadingRecords(true);
    setRecordsError(null);
    try {
      const url = new URL("/monthly-figures", API_BASE);
      url.searchParams.set("page", "1");
      url.searchParams.set("page_size", "20");

      const response = await fetch(url.toString(), { cache: "no-store" });
      if (!response.ok) {
        throw new Error(
          `Unable to pull monthly figures (${response.status}).`
        );
      }
      const data = (await response.json()) as RawPostRecord[];
      setRecords(Array.isArray(data) ? data : []);
    } catch (error) {
      setRecordsError(
        error instanceof Error
          ? error.message
          : "Unable to pull monthly figures."
      );
    } finally {
      setIsLoadingRecords(false);
    }
  }, []);

  useEffect(() => {
    fetchMonthlyFigures();
  }, [fetchMonthlyFigures]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitError(null);
    setStatusMessage(null);
    setJobResult(null);

    const month = givenMonth.trim();
    const field = fieldOfExcellence.trim();
    if (!month || !field) {
      setSubmitError("Month and field of excellence are required.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/call_api`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ai_type: "MONTHLY_FIGURES",
          input: {
            given_month: month,
            field_of_excellence: field,
          },
        }),
      });

      if (!response.ok) {
        const detail = await getErrorMessage(response);
        throw new Error(detail ?? `Unable to queue job (${response.status}).`);
      }

      const data = (await response.json()) as CallApiSuccess;
      setJobResult(data);
      setStatusMessage("Monthly figures job queued. Pull data to see updates.");
      await fetchMonthlyFigures();
    } catch (error) {
      setSubmitError(
        error instanceof Error
          ? error.message
          : "Unable to submit monthly figures request."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
      <section className="neon-panel rounded-3xl p-6 md:p-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <span className="neon-pill">Monthly figures</span>
            <h1 className="mt-4 font-display text-3xl font-semibold sm:text-4xl">
              Create new monthly figures
            </h1>
            <p className="mt-3 text-sm text-muted">
              Queue a monthly figures generation job, then pull latest records.
            </p>
          </div>
          <Link className="neon-button neon-button-ghost" href="/prominent_figures">
            Back to posts
          </Link>
        </div>

        <form className="mt-8 grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
          <label className="flex flex-col gap-2 text-sm font-semibold">
            <span className="text-soft">Given month</span>
            <select
              className="neon-input"
              value={givenMonth}
              onChange={(event) => setGivenMonth(event.target.value)}
            >
              {MONTHS.map((month) => (
                <option key={month} value={month}>
                  {month}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm font-semibold">
            <span className="text-soft">Field of excellence</span>
            <input
              className="neon-input"
              value={fieldOfExcellence}
              onChange={(event) => setFieldOfExcellence(event.target.value)}
              placeholder="Movies"
              type="text"
            />
          </label>

          <div className="sm:col-span-2 flex flex-wrap items-center gap-3">
            <button className="neon-button neon-button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Queueing..." : "Queue Monthly Figures"}
            </button>
            <button
              className="neon-button neon-button-ghost"
              type="button"
              onClick={fetchMonthlyFigures}
              disabled={isLoadingRecords}
            >
              {isLoadingRecords ? "Pulling..." : "Pull Latest Figures"}
            </button>
          </div>
        </form>

        {statusMessage && (
          <p className="mt-4 rounded-2xl border border-emerald-300/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
            {statusMessage}
          </p>
        )}
        {submitError && (
          <p className="mt-4 rounded-2xl border border-rose-300/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {submitError}
          </p>
        )}
        {jobResult && (
          <div className="mt-4 rounded-2xl border border-white/15 bg-black/20 px-4 py-3 text-sm text-soft">
            <p>
              Job ID: <span className="font-mono text-emerald-200">{jobResult.job_id}</span>
            </p>
            <p className="mt-1">
              Status: <span className="font-semibold text-emerald-100">{jobResult.status}</span>
            </p>
          </div>
        )}
      </section>

      <section className="neon-panel rounded-3xl p-5 md:p-7">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-soft">
              Pulled monthly figures
            </p>
            <p className="text-xs text-muted">
              Latest records from backend monthly figures endpoint.
            </p>
          </div>
          <p className="text-xs text-muted">{records.length} record(s)</p>
        </div>

        {recordsError && (
          <div className="mt-4 rounded-2xl border border-rose-300/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {recordsError}
          </div>
        )}

        <div className="mt-6 overflow-x-auto">
          {records.length === 0 ? (
            <p className="text-sm text-soft">
              {isLoadingRecords ? "Pulling monthly figures..." : "No monthly figures found yet."}
            </p>
          ) : (
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-white/10 text-xs uppercase tracking-[0.3em] text-soft">
                <tr>
                  <th className="py-3 pr-6">Code</th>
                  <th className="py-3 pr-6">Name</th>
                  <th className="py-3 pr-6">Country</th>
                  <th className="py-3 pr-6">DOB</th>
                  <th className="py-3 pr-6">Field</th>
                  <th className="py-3">Added</th>
                </tr>
              </thead>
              <tbody>
                {records.map((item) => {
                  const key = item._id ?? item.id ?? item.code ?? item.name ?? "row";
                  return (
                    <tr key={key} className="border-b border-white/10 last:border-b-0">
                      <td className="py-4 pr-6 align-top font-mono text-xs text-soft">
                        {fallback(item.code)}
                      </td>
                      <td className="py-4 pr-6 align-top">{fallback(item.name)}</td>
                      <td className="py-4 pr-6 align-top text-xs text-muted">
                        {fallback(item.country)}
                      </td>
                      <td className="py-4 pr-6 align-top text-xs text-muted">
                        {fallback(item.dob)}
                      </td>
                      <td className="py-4 pr-6 align-top text-xs text-muted">
                        {fallback(item.excellence_field)}
                      </td>
                      <td className="py-4 align-top text-xs text-soft">
                        {formatDate(item.added_on)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}
