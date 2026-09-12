import { Calculator, Flame, Info } from "lucide-react";
import type { OpportunityRead } from "@/features/opportunities/types";
import {
  SELLER_PRESSURE_LABELS,
  formatEuros,
  formatPercent,
  sellerPressureVariant,
} from "@/features/opportunities/format";

type OpportunityValuationPanelProps = {
  opportunity: OpportunityRead;
};

export function OpportunityValuationPanel({
  opportunity,
}: OpportunityValuationPanelProps) {
  const pressureVariant = sellerPressureVariant(
    opportunity.seller_pressure_level,
  );

  return (
    <section
      role="region"
      aria-label="Valoración económica y proyección financiera"
      className="space-y-5 rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] p-5"
    >
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-4">
        <div>
          <h3 className="font-display text-base font-bold text-[var(--foreground)]">
            Valoración Económica y Proyección de Margen
          </h3>
          <p className="text-xs text-[var(--muted)]">
            Intervalos de confianza y estructura de costes según marco ITP
            España y DGT (Plan Maestro §19).
          </p>
        </div>

        {/* Seller Pressure Badge */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--muted)]">Presión Vendedor:</span>
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
              pressureVariant === "danger"
                ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                : pressureVariant === "warning"
                  ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                  : "bg-slate-500/10 text-slate-600 dark:text-slate-400"
            }`}
          >
            <Flame size={13} aria-hidden />
            {SELLER_PRESSURE_LABELS[opportunity.seller_pressure_level]}
          </span>
        </div>
      </header>

      {/* Grid de precios principales */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-3">
          <span className="text-[0.6875rem] font-medium text-[var(--muted)]">
            Precio Pedido (Asking)
          </span>
          <p className="mt-1 font-mono text-base font-bold text-[var(--foreground)]">
            {formatEuros(opportunity.asking_price)}
          </p>
        </div>

        <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-3">
          <span className="text-[0.6875rem] font-medium text-[var(--muted)]">
            Valor Mercado Est.
          </span>
          <p className="mt-1 font-mono text-base font-bold text-[var(--foreground)]">
            {formatEuros(opportunity.estimated_market_price)}
          </p>
        </div>

        <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-3">
          <span className="text-[0.6875rem] font-medium text-[var(--muted)]">
            Venta Rápida Proyectada
          </span>
          <p className="mt-1 font-mono text-base font-bold text-amber-600 dark:text-amber-400">
            {formatEuros(opportunity.estimated_fast_sale_price)}
          </p>
        </div>

        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3">
          <span className="text-[0.6875rem] font-semibold text-emerald-700 dark:text-emerald-300">
            Compra Objetivo Sugerida
          </span>
          <p className="mt-1 font-mono text-base font-bold text-emerald-600 dark:text-emerald-400">
            {formatEuros(opportunity.target_purchase_price)}
          </p>
        </div>
      </div>

      {/* Desglose de Costes */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-4">
        <h4 className="flex items-center gap-1.5 text-xs font-bold tracking-wider text-[var(--foreground)] uppercase">
          <Calculator size={14} aria-hidden />
          Estructura de Adquisición y Preparación
        </h4>

        <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-4">
          <div>
            <span className="text-[var(--muted)]">ITP (4% mod.):</span>
            <p className="font-mono font-medium text-[var(--foreground)]">
              {formatEuros(opportunity.estimated_tax)}
            </p>
          </div>
          <div>
            <span className="text-[var(--muted)]">Tasa DGT (55,70€):</span>
            <p className="font-mono font-medium text-[var(--foreground)]">
              {formatEuros(opportunity.estimated_transfer_cost)}
            </p>
          </div>
          <div>
            <span className="text-[var(--muted)]">Coste Preparación:</span>
            <p className="font-mono font-medium text-[var(--foreground)]">
              {formatEuros(opportunity.estimated_preparation_cost)}
            </p>
          </div>
          <div>
            <span className="text-[var(--muted)]">Reparaciones Previstas:</span>
            <p className="font-mono font-medium text-[var(--foreground)]">
              {formatEuros(opportunity.estimated_repair_min)} –{" "}
              {formatEuros(opportunity.estimated_repair_max)}
            </p>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between border-t border-[var(--border)] pt-2 text-xs">
          <span className="font-semibold text-[var(--foreground)]">
            Coste Total Invertido Proyectado [Mín – Máx]:
          </span>
          <span className="font-mono font-bold text-[var(--foreground)]">
            {formatEuros(opportunity.estimated_total_cost_min)} –{" "}
            {formatEuros(opportunity.estimated_total_cost_max)}
          </span>
        </div>
      </div>

      {/* Rentabilidad Proyectada e Intervalos */}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-4">
          <span className="text-xs font-semibold text-[var(--muted)]">
            Margen Neto Proyectado [Intervalo]
          </span>
          <p className="mt-1 font-mono text-lg font-bold text-[var(--foreground)]">
            {formatEuros(opportunity.estimated_margin_min)} a{" "}
            {formatEuros(opportunity.estimated_margin_max)}
          </p>
          <p className="mt-1 text-[0.6875rem] text-[var(--muted)]">
            Calculado contra el precio de salida rápida (sin especulación).
          </p>
        </div>

        <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-4">
          <span className="text-xs font-semibold text-[var(--muted)]">
            ROI Neto Estimado [Intervalo]
          </span>
          <p className="mt-1 font-mono text-lg font-bold text-emerald-600 dark:text-emerald-400">
            {formatPercent(opportunity.estimated_roi_min)} a{" "}
            {formatPercent(opportunity.estimated_roi_max)}
          </p>
          <p className="mt-1 text-[0.6875rem] text-[var(--muted)]">
            Retorno sobre el capital total arriesgado (compra + trámites +
            preparación).
          </p>
        </div>
      </div>

      {/* Motivos de presión del vendedor si existen */}
      {opportunity.seller_pressure_reasons &&
        opportunity.seller_pressure_reasons.length > 0 && (
          <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-hover)] p-3 text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-[var(--foreground)]">
              <Info size={14} aria-hidden />
              <span>Factores de negociación observados:</span>
            </div>
            <ul className="mt-1.5 list-inside list-disc space-y-0.5 text-[var(--muted)]">
              {opportunity.seller_pressure_reasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
    </section>
  );
}
