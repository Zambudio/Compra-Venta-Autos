import { describe, expect, test } from "vitest";

import {
  CLASSIFICATION_LABELS,
  COMPONENT_LABELS,
  FREQUENCY_LABELS,
  SEVERITY_LABELS,
  SOURCE_TYPE_LABELS,
  STATUS_LABELS,
  TRUST_LEVEL_LABELS,
  classificationBadgeTone,
  formatEuro,
  severityBadgeTone,
  trustLevelBadgeTone,
} from "./format";

describe("knowledge format helpers", () => {
  test("defines labels for components, severities and frequencies", () => {
    expect(COMPONENT_LABELS.TIMING_SYSTEM).toContain("Distribución");
    expect(COMPONENT_LABELS.TURBOCHARGER).toContain("Turbo");
    expect(COMPONENT_LABELS.ENGINE_INTERNAL).toContain("Motor interno");

    expect(SEVERITY_LABELS.CRITICAL).toContain("Crítica");
    expect(SEVERITY_LABELS.HIGH).toContain("Alta");
    expect(SEVERITY_LABELS.MEDIUM).toContain("Media");
    expect(SEVERITY_LABELS.LOW).toContain("Baja");

    expect(FREQUENCY_LABELS.SYSTEMIC).toContain("Sistémica");
    expect(FREQUENCY_LABELS.FREQUENT).toContain("Frecuente");
    expect(FREQUENCY_LABELS.OCCASIONAL).toContain("Ocasional");
    expect(FREQUENCY_LABELS.RARE).toContain("Rara");
  });

  test("defines labels for status, trust levels, source types and classifications", () => {
    expect(STATUS_LABELS.VERIFIED).toContain("Verificado");
    expect(STATUS_LABELS.DRAFT).toContain("Borrador");

    expect(TRUST_LEVEL_LABELS.A).toContain("Nivel A");
    expect(TRUST_LEVEL_LABELS.B).toContain("Nivel B");
    expect(TRUST_LEVEL_LABELS.C).toContain("Nivel C");
    expect(TRUST_LEVEL_LABELS.D).toContain("Nivel D");

    expect(SOURCE_TYPE_LABELS.OFFICIAL_RECALL).toContain("Recall");
    expect(CLASSIFICATION_LABELS.WHITELIST).toContain("Lista Blanca");
    expect(CLASSIFICATION_LABELS.WATCHLIST).toContain("Bajo Observación");
    expect(CLASSIFICATION_LABELS.BLACKLIST).toContain("Lista Negra");
  });

  test("computes correct badge tones", () => {
    expect(severityBadgeTone("CRITICAL")).toBe("danger");
    expect(severityBadgeTone("HIGH")).toBe("warning");
    expect(severityBadgeTone("MEDIUM")).toBe("neutral");
    expect(severityBadgeTone("LOW")).toBe("neutral");

    expect(classificationBadgeTone("WHITELIST")).toBe("success");
    expect(classificationBadgeTone("WATCHLIST")).toBe("warning");
    expect(classificationBadgeTone("BLACKLIST")).toBe("danger");
    expect(classificationBadgeTone("UNKNOWN")).toBe("neutral");

    expect(trustLevelBadgeTone("A")).toBe("success");
    expect(trustLevelBadgeTone("B")).toBe("neutral");
    expect(trustLevelBadgeTone("C")).toBe("warning");
    expect(trustLevelBadgeTone("D")).toBe("neutral");
  });

  test("formats euro currency amounts", () => {
    expect(formatEuro(null)).toBe("—");
    expect(formatEuro(undefined)).toBe("—");
    expect(formatEuro("invalid")).toBe("—");
    expect(formatEuro(1500)).toContain("€");
    expect(formatEuro(1500)).toMatch(/1.?500/);
    expect(formatEuro("2500")).toContain("€");
    expect(formatEuro("2500")).toMatch(/2.?500/);
  });
});
