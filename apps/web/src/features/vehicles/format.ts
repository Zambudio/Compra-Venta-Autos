export {
  formatPrice,
  formatKm,
  formatDate,
  FUEL_LABELS,
  TRANSMISSION_LABELS,
  STATUS_LABELS,
} from "@/features/listings/format";

export function formatConfidence(score: string | number): string {
  const num = typeof score === "string" ? Number(score) : score;
  if (Number.isNaN(num)) return "0%";
  return `${Math.round(num * 100)}%`;
}

export function confidenceBadgeVariant(
  score: string | number,
): "neutral" | "success" | "warning" | "danger" {
  const num = typeof score === "string" ? Number(score) : score;
  if (num >= 0.8) return "success";
  if (num >= 0.6) return "warning";
  return "danger";
}
