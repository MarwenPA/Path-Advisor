/**
 * Thin fetch wrapper for the Django REST API.
 *
 * Story 1.1 seed: base URL + JSON helpers + CSRF header pass-through.
 * Story 1.3 extension: parses RFC 7807 Problem Details so feature code can read
 * `error.detail` / `error.type` and map them to user-facing copy.
 * Story 1.5: default 15-second timeout (`AbortSignal.timeout`) so a hanging
 * upstream never freezes the UI; callers needing longer can pass their own
 * `signal` in the request init.
 *
 * Rule (cf. story 1.1 §4.4): no component should call `fetch` directly — everything
 * goes through this module.
 */

const DEFAULT_TIMEOUT_MS = 15_000;

// Two URLs because Server Components run inside the `web` container and must reach
// the API via the Docker network (http://api:8000), while Client Components run in
// the user's browser and need a host-reachable URL (http://localhost:8000 in dev).
const API_BASE_URL =
  typeof window === "undefined"
    ? (process.env.API_URL_SERVER ?? "http://api:8000")
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: Record<string, unknown>;
}

export class ApiError extends Error {
  readonly status: number;
  readonly problem: ProblemDetails | null;

  constructor(status: number, message: string, problem: ProblemDetails | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

export interface ApiRequestInit extends Omit<RequestInit, "body"> {
  body?: unknown;
  csrfToken?: string;
}

export async function apiFetch<T>(path: string, init: ApiRequestInit = {}): Promise<T> {
  const { body, csrfToken, headers, signal, ...rest } = init;
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  // Story 1.5 §AC10: default 15s timeout via AbortSignal. Callers wanting a
  // longer cap (Story 1.11 GDPR export polling, future long-running ops)
  // pass their own `signal`. `AbortSignal.any` (Node 22 / browsers Q4 2024+)
  // composes caller's signal with our timeout — if either fires, the fetch
  // aborts. On older runtimes we fall back to a manual AbortController so
  // the 15s timeout always applies even when a caller passes their own
  // signal (code-review P9 — Story 1.5 review 2026-05-27).
  const timeoutSignal = AbortSignal.timeout(DEFAULT_TIMEOUT_MS);
  let effectiveSignal: AbortSignal;
  if (!signal) {
    effectiveSignal = timeoutSignal;
  } else if (typeof AbortSignal.any === "function") {
    effectiveSignal = AbortSignal.any([signal, timeoutSignal]);
  } else {
    const composed = new AbortController();
    const propagate = (src: AbortSignal) => () => composed.abort(src.reason);
    if (signal.aborted) composed.abort(signal.reason);
    else signal.addEventListener("abort", propagate(signal), { once: true });
    if (timeoutSignal.aborted) composed.abort(timeoutSignal.reason);
    else timeoutSignal.addEventListener("abort", propagate(timeoutSignal), { once: true });
    effectiveSignal = composed.signal;
  }

  const response = await fetch(url, {
    ...rest,
    credentials: "include",
    signal: effectiveSignal,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const contentType = response.headers.get("Content-Type") ?? "";
    let problem: ProblemDetails | null = null;
    if (
      contentType.includes("application/problem+json") ||
      contentType.includes("application/json")
    ) {
      try {
        problem = (await response.json()) as ProblemDetails;
      } catch {
        problem = null;
      }
    }
    throw new ApiError(
      response.status,
      problem?.detail ?? `API ${response.status} ${response.statusText}`,
      problem,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/**
 * Read the CSRF cookie set by `GET /api/v1/auth/csrf/` (Story 1.3 §T3).
 * Returns `null` if the cookie has not been seeded yet (caller should `await
 * fetchCsrfToken()` first).
 */
export function readCsrfCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match?.[1] ?? null;
}
