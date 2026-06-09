import { describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => {
  const requestInterceptor = { current: null };
  const create = vi.fn(() => ({
    interceptors: {
      request: {
        use: vi.fn((fn) => {
          requestInterceptor.current = fn;
        }),
      },
    },
  }));
  return { requestInterceptor, create };
});

vi.mock("axios", () => ({
  default: {
    create: mocks.create,
  },
}));

describe("apiClient", () => {
  it("crea el cliente con la baseURL esperada", async () => {
    const { default: apiClient } = await import("../../../src/services/apiClient");

    expect(mocks.create).toHaveBeenCalledWith({
      baseURL: "http://127.0.0.1:8000/api",
      headers: { "Content-Type": "application/json" },
    });
    expect(apiClient).toBeDefined();
  });

  it("agrega Authorization cuando existe token", async () => {
    localStorage.setItem("auth_token", "abc123");
    await import("../../../src/services/apiClient");

    const config = mocks.requestInterceptor.current({ headers: {} });

    expect(config.headers.Authorization).toBe("Bearer abc123");
  });
});