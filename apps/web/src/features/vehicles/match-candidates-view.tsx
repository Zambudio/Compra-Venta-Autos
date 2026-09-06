import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, CheckCircle2, ChevronRight, RefreshCw, Sparkles, X } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  confirmMatchCandidate,
  generateMatchCandidates,
  getMatchCandidates,
  rejectMatchCandidate,
} from "@/features/vehicles/api";
import {
  confidenceBadgeVariant,
  formatConfidence,
  formatDate,
  formatKm,
  formatPrice,
} from "@/features/vehicles/format";
import type { MatchCandidate } from "@/features/vehicles/types";

export function MatchCandidatesView() {
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState<string | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["match-candidates", "PENDING"],
    queryFn: () => getMatchCandidates("PENDING", 1, 50),
  });

  const generateMutation = useMutation({
    mutationFn: generateMatchCandidates,
    onSuccess: (res) => {
      setFeedback(
        res.created_candidates > 0
          ? `Se han detectado ${res.created_candidates} nuevos candidatos a emparejar.`
          : "No se encontraron nuevos duplicados potenciales.",
      );
      void queryClient.invalidateQueries({ queryKey: ["match-candidates"] });
    },
    onError: () => {
      setFeedback("Error al escanear duplicados.");
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (id: string) => confirmMatchCandidate(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["match-candidates"] });
      void queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      setFeedback("Emparejamiento confirmado con éxito.");
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => rejectMatchCandidate(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["match-candidates"] });
      setFeedback("Candidato descartado.");
    },
  });

  if (isLoading) {
    return (
      <div className="flex min-h-[250px] items-center justify-center" aria-live="polite">
        <p className="text-sm text-[var(--muted)]">Cargando cola de deduplicación…</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4" role="alert">
        <p className="text-sm font-medium text-[var(--danger)]">
          {error instanceof Error ? error.message : "Error al cargar candidatos de matching."}
        </p>
      </div>
    );
  }

  const items = data?.items ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-[var(--foreground)]">
            Deduplicación Asistida
          </h2>
          <p className="text-sm text-[var(--muted)]">
            Revisión manual asistida para unificar anuncios de un mismo vehículo entre diferentes fuentes.
          </p>
        </div>

        <Button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="self-start sm:self-auto gap-2"
        >
          <Sparkles aria-hidden size={16} />
          {generateMutation.isPending ? "Escaneando…" : "Escanear duplicados"}
        </Button>
      </div>

      {feedback && (
        <div
          role="status"
          aria-live="polite"
          className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-3 text-xs text-[var(--foreground)] flex items-center justify-between"
        >
          <span>{feedback}</span>
          <button
            type="button"
            onClick={() => setFeedback(null)}
            className="text-[var(--muted)] hover:text-[var(--foreground)] ml-2"
            aria-label="Cerrar notificación"
          >
            <X aria-hidden size={14} />
          </button>
        </div>
      )}

      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-[var(--radius)] border border-[var(--border)] bg-white p-12 text-center">
          <CheckCircle2 aria-hidden size={40} className="text-[var(--success)]" />
          <h3 className="text-base font-bold text-[var(--foreground)]">
            Cola de revisión al día
          </h3>
          <p className="max-w-md text-sm text-[var(--muted)]">
            No hay candidatos duplicados pendientes de confirmación. Puedes ejecutar un escaneo para buscar nuevas coincidencias entre los anuncios importados.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4" aria-label="Lista de candidatos a emparejar">
          {items.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              isConfirming={confirmMutation.isPending && confirmMutation.variables === candidate.id}
              isRejecting={rejectMutation.isPending && rejectMutation.variables === candidate.id}
              onConfirm={() => confirmMutation.mutate(candidate.id)}
              onReject={() => rejectMutation.mutate(candidate.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

type CandidateCardProps = {
  candidate: MatchCandidate;
  isConfirming: boolean;
  isRejecting: boolean;
  onConfirm: () => void;
  onReject: () => void;
};

function CandidateCard({
  candidate,
  isConfirming,
  isRejecting,
  onConfirm,
  onReject,
}: CandidateCardProps) {
  const la = candidate.listing_a;
  const lb = candidate.listing_b;
  const confidencePercent = formatConfidence(candidate.confidence_score);

  return (
    <article className="flex flex-col gap-4 rounded-[var(--radius)] border border-[var(--border)] bg-white p-5 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
        <div className="flex items-center gap-2">
          <Badge tone={confidenceBadgeVariant(candidate.confidence_score)}>
            Similitud {confidencePercent}
          </Badge>
          <span className="text-xs text-[var(--muted)]">
            Detectado el {formatDate(candidate.created_at)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onReject}
            disabled={isRejecting || isConfirming}
            className="inline-flex min-h-9 items-center gap-1.5 rounded-[var(--radius)] border border-[var(--border)] bg-white px-3 text-xs font-medium text-[var(--danger)] transition-colors hover:bg-red-50 disabled:opacity-50"
            aria-label={`Descartar coincidencia ${candidate.id}`}
          >
            <X aria-hidden size={14} />
            {isRejecting ? "Descartando…" : "Descartar"}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isConfirming || isRejecting}
            className="inline-flex min-h-9 items-center gap-1.5 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-medium text-white transition-colors hover:bg-[var(--accent-hover)] disabled:opacity-50"
            aria-label={`Confirmar coincidencia ${candidate.id}`}
          >
            <Check aria-hidden size={14} />
            {isConfirming ? "Confirmando…" : "Confirmar (1 clic)"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Anuncio A */}
        <div className="rounded-[var(--radius)] bg-[var(--surface)] p-3">
          <span className="text-xs font-semibold text-[var(--muted)]">Anuncio A</span>
          {la ? (
            <div className="mt-1 flex flex-col gap-1 text-xs">
              <p className="font-bold text-sm text-[var(--foreground)]">
                {la.brand} {la.model} ({la.year})
              </p>
              <p className="text-[var(--foreground)] font-semibold">
                {formatPrice(la.price_amount, la.price_currency)} • {formatKm(la.mileage_km)}
              </p>
              <p className="text-[var(--muted)]">
                Ref: {la.external_id} {la.province ? `• ${la.province}` : ""}
              </p>
            </div>
          ) : (
            <p className="mt-1 text-xs text-[var(--muted)]">ID: {candidate.listing_a_id}</p>
          )}
        </div>

        {/* Anuncio B */}
        <div className="rounded-[var(--radius)] bg-[var(--surface)] p-3">
          <span className="text-xs font-semibold text-[var(--muted)]">Anuncio B</span>
          {lb ? (
            <div className="mt-1 flex flex-col gap-1 text-xs">
              <p className="font-bold text-sm text-[var(--foreground)]">
                {lb.brand} {lb.model} ({lb.year})
              </p>
              <p className="text-[var(--foreground)] font-semibold">
                {formatPrice(lb.price_amount, lb.price_currency)} • {formatKm(lb.mileage_km)}
              </p>
              <p className="text-[var(--muted)]">
                Ref: {lb.external_id} {lb.province ? `• ${lb.province}` : ""}
              </p>
            </div>
          ) : (
            <p className="mt-1 text-xs text-[var(--muted)]">ID: {candidate.listing_b_id}</p>
          )}
        </div>
      </div>
    </article>
  );
}
