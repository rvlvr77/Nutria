import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiBaseUrl, apiFetch } from "./api";

function mockFetch(status: number, payload: unknown): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("apiBaseUrl", () => {
  it("uses NEXT_PUBLIC_API_URL in the browser and strips trailing slash", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.nutriai.app/api/");
    expect(apiBaseUrl()).toBe("https://api.nutriai.app/api");
  });
});

describe("apiFetch", () => {
  it("unwraps data from a success envelope", async () => {
    mockFetch(200, { success: true, data: { status: "ok" } });
    await expect(apiFetch<{ status: string }>("/health")).resolves.toEqual({ status: "ok" });
  });

  it("sends JSON body and bearer token", async () => {
    mockFetch(200, { success: true, data: null });
    await apiFetch("/x", { method: "POST", body: { a: 1 }, token: "tkn" });
    const [, init] = vi.mocked(fetch).mock.calls[0]!;
    const headers = init?.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer tkn");
    expect(headers["Content-Type"]).toBe("application/json");
    expect(init?.body).toBe('{"a":1}');
  });

  it("throws ApiError with backend code on error envelope", async () => {
    mockFetch(404, { success: false, error: { code: "not_found", message: "No existe" } });
    const err = await apiFetch("/plans/1").catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 404, code: "not_found", message: "No existe" });
  });

  it("maps network failures to network_error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fail")));
    await expect(apiFetch("/health")).rejects.toMatchObject({ code: "network_error", status: 0 });
  });

  it("rejects non-JSON responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>", { status: 502 })));
    await expect(apiFetch("/health")).rejects.toMatchObject({ code: "invalid_response" });
  });
});
