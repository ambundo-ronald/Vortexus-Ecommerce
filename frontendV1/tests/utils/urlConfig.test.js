import {
  buildApiRoot,
  buildMediaUrl,
  normalizeOrigin,
  normalizePath
} from "../../src/utils/urlConfig";

describe("runtime URL configuration", () => {
  test("normalizes origins and API paths", () => {
    expect(normalizeOrigin(" https://api.example.com/// ")).toBe("https://api.example.com");
    expect(normalizePath("api/v1/")).toBe("/api/v1");
  });

  test("uses a same-origin API root when no public API origin is configured", () => {
    expect(buildApiRoot("", "/api/v1")).toBe("/api/v1");
  });

  test("does not duplicate a prefix included in the configured API URL", () => {
    expect(buildApiRoot("https://api.example.com/api/v1/", "/api/v1")).toBe(
      "https://api.example.com/api/v1"
    );
  });

  test("resolves backend media against an absolute API origin", () => {
    expect(buildMediaUrl("/media/products/pump.webp", "https://api.example.com")).toBe(
      "https://api.example.com/media/products/pump.webp"
    );
    expect(buildMediaUrl("/media/products/pump.webp", "")).toBe("/media/products/pump.webp");
  });
});
