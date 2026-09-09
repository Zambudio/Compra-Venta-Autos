import type {
  ConfidenceLevel,
  OpportunityStatus,
  ScoringComponentKey,
  SellerPressureLevel,
} from "@/features/opportunities/types";

export {
  formatPrice,
  formatKm,
  formatDate,
  FUEL_LABELS,
  TRANSMISSION_LABELS,
} from "@/features/listings/format";

export const OPPORTUNITY_STATUS_LABELS: Record<OpportunityStatus, string> = {
  IDENTIFIED: "Identificada",
  ANALYZING: "En análisis",
  VALIDATED: "Validada",
  DISCARDED: "Descartada",
  PURCHASED: "Comprada",
  SOLD: "Vendida",
};

export const SELLER_PRESSURE_LABELS: Record<SellerPressureLevel, string> = {
  LOW: "Presión baja",
  MEDIUM: "Presión media",
  HIGH: "Presión alta",
};

export const CONFIDENCE_LEVEL_LABELS: Record<ConfidenceLevel, string> = {
  LOW: "Baja",
  MEDIUM: "Media",
  HIGH: "Alta",
};

export const COMPONENT_LABELS: Record<ScoringComponentKey, string> = {
  price: "Precio vs Mercado",
  reliability: "Fiabilidad Modelo",
  liquidity: "Liquidez de Venta",
  mechanical_risk: "Riesgo Mecánico",
  mileage: "Kilometraje",
  age: "Antigüedad",
  history: "Historial de Precios",
  condition: "Estado General",
  listing_age: "Días en Venta",
};

export function formatEuros(amount: string | number | null | undefined): string {
  if (amount === null || amount === undefined || amount === "") return "— €";
  const val = typeof amount === "string" ? Number(amount) : amount;
  if (Number.isNaN(val)) return "— €";
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(val);
}

export function formatPercent(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "— %";
  const val = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(val)) return "— %";
  return `${val >= 0 ? "+" : ""}${val.toFixed(1)}%`;
}

export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return `${Math.round(score)} / 100`;
}

export function scoreColorVariant(score: number): "success" | "warning" | "danger" {
  if (score >= 70) return "success";
  if (score >= 50) return "warning";
  return "danger";
}

export function sellerPressureVariant(
  level: SellerPressureLevel,
): "neutral" | "warning" | "danger" {
  if (level === "HIGH") return "danger";
  if (level === "MEDIUM") return "warning";
  return "neutral";
}
