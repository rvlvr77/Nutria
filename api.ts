/**
 * Cliente HTTP tipado para la API de NutriAI.
 * Todas las respuestas siguen el envelope { success, data?, error?: { code, message } }.
 */

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data?: T;
  error?: ApiErrorBody;
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: unknown;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.details = body.details;
  }
}

/** URL base: en servidor usa la red interna de Docker; en navegador, la pública. */
export function apiBaseUrl(): string {
  const isServer = typeof window === "undefined";
  const url =
    (isServer ? process.env.INTERNAL_API_URL : undefined) ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000/api";
  return url.replace(/\/+$/, "");
}

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  token?: string;
  timeoutMs?: number;
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, token, timeoutMs = 15_000, headers, ...init } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`, {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    const aborted = err instanceof DOMException && err.name === "AbortError";
    throw new ApiError(0, {
      code: aborted ? "timeout" : "network_error",
      message: aborted ? "La solicitud tardó demasiado" : "No se pudo conectar con el servidor",
    });
  } finally {
    clearTimeout(timer);
  }

  let envelope: ApiEnvelope<T>;
  try {
    envelope = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiError(response.status, {
      code: "invalid_response",
      message: "Respuesta inválida del servidor",
    });
  }

  if (!response.ok || !envelope.success) {
    throw new ApiError(
      response.status,
      envelope.error ?? { code: "unknown_error", message: "Error desconocido" },
    );
  }
  return envelope.data as T;
}
