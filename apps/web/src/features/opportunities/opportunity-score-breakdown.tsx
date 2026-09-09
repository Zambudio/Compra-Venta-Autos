import { CheckCircle2, HelpCircle, ShieldAlert } from "lucide-react";
import type {
  OpportunityScoreRead,
  ScoringComponentKey,
} from "@/features/opportunities/types";
import {
  COMPONENT_LABELS,
  CONFIDENCE_LEVEL_LABELS,
  formatScore,
  scoreColorVariant,
} from "@/features/opportunities/format";

type OpportunityScoreBreakdownProps = {
  score: OpportunityScoreRead | null | undefined;
};

const ORDERED_COMPONENTS: ScoringComponentKey[] = [
  "price",
  "reliability",
  "liquidity",
  "mechanical_risk",
  "mileage",
  "age",
  "history",
  "condition",
  "listing_age",
];

export function OpportunityScoreBreakdown({
  score,
}: OpportunityScoreBreakdownProps) {
  if (!score) {
    return (
      <div
        role="region"
        aria-label="Desglose de scoring"
        className="rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] p-4 text-center text-sm text-[var(--muted)]"
      >
        <p>No hay puntuación calculada para esta oportunidad todavía.</p>
      </div>
    );
  }

  const total = Number(score.total_score ?? score.score_total ?? 0);
  const variant = scoreColorVariant(total);

  return (
    <section
      role="region"
      aria-label="Desglose determinista de scoring"
      className="space-y-4 rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] p-5"
    >
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-4">
        <div>
          <h3 className="font-display text-base font-bold text-[var(--foreground)]">
            Scoring Multicriterio Determinista
          </h3>
          <p className="text-xs text-[var(--muted)]">
            Algoritmo explicable de 9 componentes ponderados (Plan Maestro §18).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs text-[var(--muted)]">Confianza: </span>
            <span className="text-xs font-semibold text-[var(--foreground)]">
              {CONFIDENCE_LEVEL_LABELS[score.confidence_level ?? "MEDIUM"]}
              {score.confidence_score !== undefined
                ? ` (${Math.round(score.confidence_score * 100)}%)`
                : ""}
            </span>
          </div>
          <div
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-bold ${
              variant === "success"
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                : variant === "warning"
                  ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                  : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
            }`}
          >
            {variant === "success" ? (
              <CheckCircle2 size={16} aria-hidden />
            ) : variant === "warning" ? (
              <HelpCircle size={16} aria-hidden />
            ) : (
              <ShieldAlert size={16} aria-hidden />
            )}
            <span>{formatScore(total)}</span>
          </div>
        </div>
      </header>

      <div className="grid gap-3 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {ORDERED_COMPONENTS.map((key) => {
          const breakdown = score.score_breakdown[key];
          const label = COMPONENT_LABELS[key] ?? key;
          const weightPercent = breakdown ? Math.round(Number(breakdown.weight) * 100) : 0;
          const subScore = breakdown ? Math.round(Number(breakdown.score ?? breakdown.sub_score ?? 0)) : 0;
          const weightedPts = breakdown ? Number(breakdown.weighted_score ?? breakdown.weighted_points ?? 0).toFixed(1) : "0.0";
          const reason = breakdown?.explanation || breakdown?.reason || "Sin justificación disponible";

          return (
            <article
              key={key}
              className="flex flex-col justify-between rounded-lg border border-[var(--border)] bg-[var(--background)] p-3.5"
            >
              <div>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[var(--foreground)]">
                    {label}
                  </span>
                  <span className="text-[var(--muted)] font-mono text-[0.6875rem]">
                    {weightPercent}% peso
                  </span>
                </div>

                {/* Progress bar */}
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[var(--surface-hover)]">
                  <div
                    role="progressbar"
                    aria-label={`Puntuación de ${label}`}
                    aria-valuenow={subScore}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    style={{ width: `${Math.min(100, Math.max(0, subScore))}%` }}
                    className={`h-full transition-all duration-300 ${
                      subScore >= 70
                        ? "bg-emerald-500"
                        : subScore >= 50
                          ? "bg-amber-500"
                          : "bg-rose-500"
                    }`}
                  />
                </div>

                <div className="mt-1.5 flex items-center justify-between text-[0.6875rem] text-[var(--muted)]">
                  <span>Subscore: {subScore}/100</span>
                  <span className="font-semibold text-[var(--foreground)]">
                    +{weightedPts} pts
                  </span>
                </div>
              </div>

              <p className="mt-2.5 rounded bg-[var(--surface)] p-2 text-[0.75rem] text-[var(--muted-soft)] leading-snug">
                {reason}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
