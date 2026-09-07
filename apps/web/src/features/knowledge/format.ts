import type {
  ClassificationStatus,
  IssueFrequency,
  IssueSeverity,
  IssueStatus,
  KnowledgeSourceType,
  SourceTrustLevel,
  VehicleComponent,
} from "./types";

export const COMPONENT_LABELS: Record<VehicleComponent, string> = {
  TIMING_SYSTEM: "Distribución (Correa / Cadena)",
  ENGINE_INTERNAL: "Motor interno (Pistones, Bloque, Culata)",
  FUEL_INJECTION: "Inyección y Combustible",
  TURBOCHARGER: "Sobrealimentación y Turbo",
  COOLING_SYSTEM: "Refrigeración y Termostato",
  EXHAUST_EMISSIONS: "Escape, FAP, EGR y AdBlue",
  TRANSMISSION_MANUAL: "Caja de cambios manual",
  TRANSMISSION_AUTOMATIC: "Caja de cambios automática",
  ELECTRICAL_HYBRID: "Sistema eléctrico e híbrido",
  BRAKING: "Sistema de frenado",
  SUSPENSION_STEERING: "Suspensión y dirección",
  CHASSIS_BODY: "Chasis y carrocería",
};

export const SEVERITY_LABELS: Record<IssueSeverity, string> = {
  LOW: "Baja (Molestia leve)",
  MEDIUM: "Media (Reparación estándar)",
  HIGH: "Alta (Avería grave / inmovilizante)",
  CRITICAL: "Crítica (Riesgo de rotura catastrófica / Seguridad)",
};

export const FREQUENCY_LABELS: Record<IssueFrequency, string> = {
  RARE: "Rara (< 2% de unidades)",
  OCCASIONAL: "Ocasional (2% - 10%)",
  FREQUENT: "Frecuente (10% - 30%)",
  SYSTEMIC: "Sistémica / Defecto de diseño (> 30%)",
};

export const STATUS_LABELS: Record<IssueStatus, string> = {
  DRAFT: "Borrador (Pendiente de evidencias)",
  REVIEWED: "En revisión técnica",
  VERIFIED: "Verificado con evidencias",
  DEPRECATED: "Obsoleto",
};

export const TRUST_LEVEL_LABELS: Record<SourceTrustLevel, string> = {
  A: "Nivel A • Oficial / Campañas de retirada (Safety Gate)",
  B: "Nivel B • Estadística independiente (TÜV, ADAC, OCU)",
  C: "Nivel C • Prensa técnica y talleres especializados",
  D: "Nivel D • Experiencia de comunidad y foros",
};

export const SOURCE_TYPE_LABELS: Record<KnowledgeSourceType, string> = {
  OFFICIAL_RECALL: "Alerta oficial de seguridad / Recall",
  STATISTICAL_REPORT: "Informe estadístico de fiabilidad",
  TECHNICAL_MEDIA: "Publicación técnica especializada",
  COMMUNITY_EXPERIENCE: "Base comunitaria contrastada",
};

export const CLASSIFICATION_LABELS: Record<ClassificationStatus, string> = {
  WHITELIST: "Lista Blanca (Recomendado)",
  WATCHLIST: "Bajo Observación (Riesgo moderado)",
  BLACKLIST: "Lista Negra (No recomendado)",
  UNKNOWN: "Sin clasificación documentada",
};

export function severityBadgeTone(
  severity: IssueSeverity,
): "danger" | "warning" | "neutral" {
  switch (severity) {
    case "CRITICAL":
      return "danger";
    case "HIGH":
      return "warning";
    case "MEDIUM":
      return "neutral";
    case "LOW":
      return "neutral";
  }
}

export function classificationBadgeTone(
  status: ClassificationStatus,
): "success" | "warning" | "danger" | "neutral" {
  switch (status) {
    case "WHITELIST":
      return "success";
    case "WATCHLIST":
      return "warning";
    case "BLACKLIST":
      return "danger";
    case "UNKNOWN":
      return "neutral";
  }
}

export function trustLevelBadgeTone(
  level: SourceTrustLevel,
): "success" | "warning" | "neutral" {
  switch (level) {
    case "A":
      return "success";
    case "B":
      return "neutral";
    case "C":
      return "warning";
    case "D":
      return "neutral";
  }
}

export function formatEuro(amount: string | number | null | undefined): string {
  if (amount == null) return "—";
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(num)) return "—";
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(num);
}
