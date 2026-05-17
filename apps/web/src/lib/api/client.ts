/**
 * Thin fetch wrapper for the Django REST API.
 *
 * Story 1.1 seed: base URL + JSON helpers + CSRF header pass-through.
 * Story 1.3 extension: parses RFC 7807 Problem Details so feature code can read
 * `error.detail` / `error.type` and map them to user-facing copy.
 * Story 1.5 will add a typed client built on top of `src/lib/api/generated/schema.ts`.
 *
 * Rule (cf. story 1.1 §4.4): no component should call `fetch` directly — everything
 * goes through this module.
 */

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
  const { body, csrfToken, headers, ...rest } = init;
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const response = await fetch(url, {
    ...rest,
    credentials: "include",
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
    if (contentType.includes("application/problem+json") || contentType.includes("application/json")) {
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
