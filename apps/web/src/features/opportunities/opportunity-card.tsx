import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Flame,
  Gauge,
  MapPin,
} from "lucide-react";
import type {
  OpportunityRead,
  OpportunityStatus,
} from "@/features/opportunities/types";
import {
  OPPORTUNITY_STATUS_LABELS,
  SELLER_PRESSURE_LABELS,
  formatEuros,
  formatKm,
  formatPercent,
  formatScore,
  scoreColorVariant,
  sellerPressureVariant,
} from "@/features/opportunities/format";
import { OpportunityScoreBreakdown } from "@/features/opportunities/opportunity-score-breakdown";
import { OpportunityValuationPanel } from "@/features/opportunities/opportunity-valuation-panel";

type OpportunityCardProps = {
  opportunity: OpportunityRead;
  onStatusChange?: (
    opportunityId: string,
    newStatus: OpportunityStatus,
  ) => Promise<void>;
  isUpdatingStatus?: boolean;
};

const ALL_STATUSES: OpportunityStatus[] = [
  "IDENTIFIED",
  "ANALYZING",
  "VALIDATED",
  "DISCARDED",
  "PURCHASED",
  "SOLD",
];

export function OpportunityCard({
  opportunity,
  onStatusChange,
  isUpdatingStatus = false,
}: OpportunityCardProps) {
  const [expanded, setExpanded] = useState(false);
  const scoreTotal = Number(
    opportunity.score?.total_score ?? opportunity.score?.score_total ?? 0,
  );
  const scoreVariant = scoreColorVariant(scoreTotal);
  const pressureVariant = sellerPressureVariant(
    opportunity.seller_pressure_level,
  );

  const title =
    opportunity.title ||
    `${opportunity.brand || "Vehículo"} ${opportunity.model || ""}`.trim() ||
    "Oportunidad sin título";

  return (
    <article
      aria-label={`Oportunidad: ${title}`}
      className="overflow-hidden rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] transition-all hover:border-[var(--border-strong)]"
    >
      <div className="p-4 sm:p-5">
        {/* Cabecera: Título + Score Badge + Status Select */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="font-display truncate text-base font-bold text-[var(--foreground)]">
                {title}
              </h2>
              {opportunity.external_url && (
                <a
                  href={opportunity.external_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-[var(--accent)] hover:underline"
                  aria-label="Ver anuncio original"
                >
                  <ExternalLink size={13} aria-hidden />
                  <span className="hidden sm:inline">Anuncio</span>
                </a>
              )}
            </div>

            <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--muted)]">
              {opportunity.year && <span>Año {opportunity.year}</span>}
              {opportunity.mileage_km !== null &&
                opportunity.mileage_km !== undefined && (
                  <span className="flex items-center gap-1">
                    <Gauge size={12} aria-hidden />
                    {formatKm(opportunity.mileage_km)}
                  </span>
                )}
              {opportunity.city && (
                <span className="flex items-center gap-1">
                  <MapPin size={12} aria-hidden />
                  {opportunity.city}
                </span>
              )}
            </div>
          </div>

          {/* Badges de Score y Presión */}
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
                pressureVariant === "danger"
                  ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                  : pressureVariant === "warning"
                    ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                    : "bg-slate-500/10 text-slate-600 dark:text-slate-400"
              }`}
            >
              <Flame size={12} aria-hidden />
              <span>
                {SELLER_PRESSURE_LABELS[opportunity.seller_pressure_level]}
              </span>
            </span>

            <div
              className={`inline-flex items-center rounded-lg px-2.5 py-1 text-sm font-bold ${
                scoreVariant === "success"
                  ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                  : scoreVariant === "warning"
                    ? "bg-amber-500/15 text-amber-600 dark:text-amber-400"
                    : "bg-rose-500/15 text-rose-600 dark:text-rose-400"
              }`}
            >
              <span className="mr-1 text-xs opacity-70">Score:</span>
              <span>{formatScore(scoreTotal)}</span>
            </div>
          </div>
        </div>

        {/* Métricas clave en tarjeta */}
        <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg border border-[var(--border)] bg-[var(--background)] p-3 sm:grid-cols-4 sm:gap-3">
          <div>
            <span className="text-[0.6875rem] text-[var(--muted)]">
              Precio Pedido
            </span>
            <p className="font-mono text-sm font-bold text-[var(--foreground)]">
              {formatEuros(opportunity.asking_price)}
            </p>
          </div>
          <div>
            <span className="text-[0.6875rem] text-[var(--muted)]">
              Venta Rápida
            </span>
            <p className="font-mono text-sm font-bold text-amber-600 dark:text-amber-400">
              {formatEuros(opportunity.estimated_fast_sale_price)}
            </p>
          </div>
          <div>
            <span className="text-[0.6875rem] text-[var(--muted)]">
              Margen Neto Proy.
            </span>
            <p className="font-mono text-sm font-bold text-[var(--foreground)]">
              {formatEuros(opportunity.estimated_margin_min)} –{" "}
              {formatEuros(opportunity.estimated_margin_max)}
            </p>
          </div>
          <div>
            <span className="text-[0.6875rem] text-[var(--muted)]">
              ROI Estimado
            </span>
            <p className="font-mono text-sm font-bold text-emerald-600 dark:text-emerald-400">
              {formatPercent(opportunity.estimated_roi_min)} –{" "}
              {formatPercent(opportunity.estimated_roi_max)}
            </p>
          </div>
        </div>

        {/* Barra inferior: Gestión de Estado + Botón Expandir Detalle */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border)] pt-3">
          <div className="flex items-center gap-2">
            <label
              htmlFor={`status-select-${opportunity.id}`}
              className="text-xs font-medium text-[var(--muted)]"
            >
              Estado:
            </label>
            <select
              id={`status-select-${opportunity.id}`}
              value={opportunity.status}
              disabled={isUpdatingStatus}
              onChange={(e) => {
                if (onStatusChange) {
                  onStatusChange(
                    opportunity.id,
                    e.target.value as OpportunityStatus,
                  );
                }
              }}
              className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2.5 py-1 text-xs font-semibold text-[var(--foreground)] focus:border-[var(--accent)] focus:outline-none"
            >
              {ALL_STATUSES.map((st) => (
                <option key={st} value={st}>
                  {OPPORTUNITY_STATUS_LABELS[st]}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            aria-expanded={expanded}
            className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold text-[var(--accent)] transition-colors hover:bg-[var(--surface-hover)]"
          >
            <span>
              {expanded ? "Ocultar análisis" : "Ver desglose detallado"}
            </span>
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {/* Sección Expandida: Paneles de Scoring y Valoración */}
      {expanded && (
        <div className="space-y-5 border-t border-[var(--border)] bg-[var(--background)] p-4 sm:p-5">
          <OpportunityScoreBreakdown score={opportunity.score} />
          <OpportunityValuationPanel opportunity={opportunity} />
        </div>
      )}
    </article>
  );
}
