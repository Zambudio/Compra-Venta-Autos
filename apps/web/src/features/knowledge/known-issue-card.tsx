import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ShieldAlert,
  Wrench,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import {
  COMPONENT_LABELS,
  formatEuro,
  FREQUENCY_LABELS,
  SEVERITY_LABELS,
  severityBadgeTone,
  STATUS_LABELS,
  TRUST_LEVEL_LABELS,
  trustLevelBadgeTone,
} from "./format";
import type { KnownIssue } from "./types";

type KnownIssueCardProps = {
  issue: KnownIssue;
};

export function KnownIssueCard({ issue }: KnownIssueCardProps) {
  const [expanded, setExpanded] = useState(false);

  const sevTone = severityBadgeTone(issue.severity);

  return (
    <article
      className="flex flex-col rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface-raised)] p-5 shadow-[var(--shadow-card)] transition-[border-color,box-shadow] duration-200 hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-raised)]"
      aria-labelledby={`issue-title-${issue.id}`}
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3
              id={`issue-title-${issue.id}`}
              className="text-base font-bold text-[var(--foreground)]"
            >
              {issue.title}
            </h3>
            <Badge tone={sevTone}>
              {SEVERITY_LABELS[issue.severity] ?? issue.severity}
            </Badge>
            {issue.has_recall_campaign && (
              <Badge tone="danger">
                <span className="inline-flex items-center gap-1">
                  <ShieldAlert aria-hidden size={12} />
                  Campaña Oficial (Recall)
                </span>
              </Badge>
            )}
            <Badge tone="neutral">
              {STATUS_LABELS[issue.status] ?? issue.status}
            </Badge>
          </div>
          <p className="text-xs text-[var(--muted)]">
            Componente: {COMPONENT_LABELS[issue.component] ?? issue.component} •{" "}
            Frecuencia: {FREQUENCY_LABELS[issue.frequency] ?? issue.frequency}
            {issue.typical_mileage_km != null && (
              <>
                {" "}
                • Kilometraje típico: ~
                {issue.typical_mileage_km.toLocaleString("es-ES")} km
              </>
            )}
          </p>
        </div>

        {/* Coste estimado */}
        <div className="text-left sm:text-right">
          <span className="text-xs text-[var(--muted)]">Coste estimado:</span>
          <p className="text-sm font-bold text-[var(--foreground)]">
            {formatEuro(issue.estimated_repair_cost_min)} –{" "}
            {formatEuro(issue.estimated_repair_cost_max)}
          </p>
        </div>
      </div>

      <p className="mt-3 text-sm leading-relaxed text-[var(--foreground)]">
        {issue.description}
      </p>

      {/* Botón expandir detalles */}
      <div className="mt-4 flex items-center justify-between border-t border-[var(--border)] pt-3">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="inline-flex items-center gap-1 text-xs font-medium text-[var(--accent)] hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]"
          aria-expanded={expanded}
          aria-controls={`issue-details-${issue.id}`}
        >
          {expanded ? (
            <>
              <ChevronUp aria-hidden size={14} /> Menos detalles
            </>
          ) : (
            <>
              <ChevronDown aria-hidden size={14} /> Síntomas, prevención y
              evidencias ({issue.evidences?.length ?? 0})
            </>
          )}
        </button>
      </div>

      {expanded && (
        <div
          id={`issue-details-${issue.id}`}
          className="mt-4 flex flex-col gap-4 rounded-[var(--radius-card)] bg-[var(--surface-inset)] p-4 text-xs"
        >
          {issue.symptoms && (
            <div>
              <span className="flex items-center gap-1 font-semibold text-[var(--foreground)]">
                <AlertTriangle
                  aria-hidden
                  size={13}
                  className="text-[var(--warning)]"
                />
                Síntomas y alertas tempranas:
              </span>
              <p className="mt-1 text-[var(--muted)]">{issue.symptoms}</p>
            </div>
          )}

          {issue.prevention && (
            <div>
              <span className="font-semibold text-[var(--foreground)]">
                Prevención y mantenimiento recomendado:
              </span>
              <p className="mt-1 text-[var(--muted)]">{issue.prevention}</p>
            </div>
          )}

          {issue.definitive_repair && (
            <div>
              <span className="flex items-center gap-1 font-semibold text-[var(--foreground)]">
                <Wrench aria-hidden size={13} />
                Solución o reparación definitiva:
              </span>
              <p className="mt-1 text-[var(--muted)]">
                {issue.definitive_repair}
              </p>
            </div>
          )}

          {issue.recall_details && (
            <div className="rounded border border-[var(--danger)]/30 bg-[var(--danger)]/5 p-2.5">
              <span className="flex items-center gap-1 font-semibold text-[var(--danger)]">
                <ShieldAlert aria-hidden size={13} />
                Detalles del Recall / Campaña:
              </span>
              <p className="mt-1 text-[var(--danger)]">
                {issue.recall_details}
              </p>
            </div>
          )}

          {/* Evidencias documentales */}
          <div>
            <span className="font-semibold text-[var(--foreground)]">
              Evidencias y Fuentes Trazables (Plan Maestro §15):
            </span>
            {issue.evidences && issue.evidences.length > 0 ? (
              <ul className="mt-2 flex flex-col gap-2">
                {issue.evidences.map((ev) => (
                  <li
                    key={ev.id}
                    className="flex flex-col gap-1 rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface-raised)] p-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {ev.source && (
                          <Badge
                            tone={trustLevelBadgeTone(ev.source.trust_level)}
                          >
                            {TRUST_LEVEL_LABELS[ev.source.trust_level] ??
                              ev.source.trust_level}
                          </Badge>
                        )}
                        <span className="font-medium text-[var(--foreground)]">
                          {ev.source?.name ?? "Fuente documental"}
                        </span>
                      </div>
                      {ev.source?.url && (
                        <a
                          href={ev.source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[var(--accent)] hover:underline"
                        >
                          Ver fuente <ExternalLink aria-hidden size={11} />
                        </a>
                      )}
                    </div>
                    <p className="text-[var(--muted)]">{ev.summary}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-1 text-[var(--muted)] italic">
                Sin evidencias trazables detalladas cargadas en esta vista.
              </p>
            )}
          </div>
        </div>
      )}
    </article>
  );
}
