const DEFAULT_BACKEND_API_BASE = "http://127.0.0.1:8000";

export const getBackendApiBase = () =>
  process.env.API_BASE_URL?.trim() ||
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ||
  DEFAULT_BACKEND_API_BASE;

export const getLogApiKey = () => process.env.LOG_API_KEY?.trim();

export const createBackendLogUrl = (path: string, search = "") => {
  const baseUrl = getBackendApiBase().replace(/\/$/, "");
  return new URL(`${baseUrl}${path}${search}`);
};
