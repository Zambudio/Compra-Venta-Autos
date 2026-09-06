import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Calculator, Calendar, Clock, DollarSign, ExternalLink, RefreshCw, ShieldAlert, Tag } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { computeVehicleMarketEstimate, getVehicle } from "@/features/vehicles/api";
import {
  confidenceBadgeVariant,
  formatConfidence,
  formatDate,
  formatKm,
  formatPrice,
  FUEL_LABELS,
  STATUS_LABELS,
  TRANSMISSION_LABELS,
} from "@/features/vehicles/format";
import type { VehicleDetail as TVehicleDetail } from "@/features/vehicles/types";

type VehicleDetailProps = {
  vehicleId: string;
  onBack: () => void;
};

export function VehicleDetail({ vehicleId, onBack }: VehicleDetailProps) {
  const queryClient = useQueryClient();

  const { data: vehicle, isLoading, isError, error } = useQuery<TVehicleDetail>({
    queryKey: ["vehicle", vehicleId],
    queryFn: () => getVehicle(vehicleId),
  });

  const estimateMutation = useMutation({
    mutationFn: () => computeVehicleMarketEstimate(vehicleId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["vehicle", vehicleId] });
      void queryClient.invalidateQueries({ queryKey: ["vehicles"] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center" aria-live="polite">
        <p className="text-sm text-[var(--muted)]">Cargando ficha del vehículo…</p>
      </div>
    );
  }

  if (isError || !vehicle) {
    return (
      <div className="flex flex-col items-start gap-4 p-6" role="alert">
        <p className="text-sm font-medium text-[var(--danger)]">
          {error instanceof Error ? error.message : "No se pudo cargar la información del vehículo."}
        </p>
        <Button onClick={onBack}>Volver a la lista</Button>
      </div>
    );
  }

  const fuel = FUEL_LABELS[vehicle.fuel_type] ?? vehicle.fuel_type;
  const transmission = TRANSMISSION_LABELS[vehicle.transmission] ?? vehicle.transmission;
  const estimate = vehicle.market_estimate;
  const history = vehicle.history;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex min-h-10 items-center gap-2 rounded-[var(--radius)] border border-[var(--border)] bg-white px-3 text-sm font-medium text-[var(--foreground)] transition-colors hover:bg-[var(--surface-hover)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]"
          aria-label="Volver al catálogo de vehículos"
        >
          <ArrowLeft aria-hidden size={16} />
          Volver
        </button>
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
            {vehicle.brand} {vehicle.model}
          </h2>
          <p className="text-xs text-[var(--muted)]">
            ID: {vehicle.id} • Registrado el {formatDate(vehicle.first_listed_at)}
          </p>
        </div>
      </div>

      {/* Grid de ficha técnica y estimación */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Ficha técnica */}
        <section
          aria-labelledby="technical-specs-title"
          className="rounded-[var(--radius)] border border-[var(--border)] bg-white p-5 shadow-xs"
        >
          <h3 id="technical-specs-title" className="mb-4 text-base font-bold text-[var(--foreground)]">
            Especificaciones Técnicas
          </h3>
          <dl className="grid grid-cols-2 gap-y-3 text-sm">
            <dt className="text-[var(--muted)]">Marca</dt>
            <dd className="font-medium text-[var(--foreground)]">{vehicle.brand}</dd>

            <dt className="text-[var(--muted)]">Modelo</dt>
            <dd className="font-medium text-[var(--foreground)]">{vehicle.model}</dd>

            {vehicle.generation && (
              <>
                <dt className="text-[var(--muted)]">Generación</dt>
                <dd className="font-medium text-[var(--foreground)]">{vehicle.generation}</dd>
              </>
            )}

            {vehicle.trim && (
              <>
                <dt className="text-[var(--muted)]">Versión / Acabado</dt>
                <dd className="font-medium text-[var(--foreground)]">{vehicle.trim}</dd>
              </>
            )}

            <dt className="text-[var(--muted)]">Año</dt>
            <dd className="font-medium text-[var(--foreground)]">{vehicle.year}</dd>

            <dt className="text-[var(--muted)]">Combustible</dt>
            <dd className="font-medium text-[var(--foreground)]">{fuel}</dd>

            <dt className="text-[var(--muted)]">Transmisión</dt>
            <dd className="font-medium text-[var(--foreground)]">{transmission}</dd>

            {vehicle.power_kw && (
              <>
                <dt className="text-[var(--muted)]">Potencia</dt>
                <dd className="font-medium text-[var(--foreground)]">{vehicle.power_kw} kW</dd>
              </>
            )}

            {vehicle.engine_code && (
              <>
                <dt className="text-[var(--muted)]">Código de Motor</dt>
                <dd className="font-medium text-[var(--foreground)]">{vehicle.engine_code}</dd>
              </>
            )}
          </dl>
        </section>

        {/* Estimación de mercado */}
        <section
          aria-labelledby="market-estimate-title"
          className="rounded-[var(--radius)] border border-[var(--border)] bg-white p-5 shadow-xs"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 id="market-estimate-title" className="text-base font-bold text-[var(--foreground)]">
              Estimación de Mercado
            </h3>
            <button
              type="button"
              onClick={() => estimateMutation.mutate()}
              disabled={estimateMutation.isPending}
              className="inline-flex items-center gap-1.5 rounded-[var(--radius)] border border-[var(--border)] px-2.5 py-1 text-xs font-medium text-[var(--muted)] hover:text-[var(--foreground)] disabled:opacity-50"
              aria-label="Recalcular estimación de mercado"
            >
              <RefreshCw
                aria-hidden
                size={12}
                className={estimateMutation.isPending ? "animate-spin" : undefined}
              />
              {estimateMutation.isPending ? "Calculando…" : "Recalcular"}
            </button>
          </div>

          {estimate ? (
            <div className="flex flex-col gap-4">
              <div>
                <p className="text-xs text-[var(--muted)]">Valor estimado de mercado</p>
                <div className="flex items-baseline gap-3">
                  <span className="text-3xl font-extrabold tracking-tight text-[var(--foreground)]">
                    {formatPrice(estimate.estimated_amount, estimate.currency)}
                  </span>
                  <Badge tone={confidenceBadgeVariant(estimate.confidence_score)}>
                    Confianza {formatConfidence(estimate.confidence_score)}
                  </Badge>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 rounded-[var(--radius)] bg-[var(--surface)] p-3 text-xs">
                <div>
                  <span className="text-[var(--muted)]">Rango razonable (P25 - P75):</span>
                  <p className="font-semibold text-[var(--foreground)]">
                    {formatPrice(estimate.low_amount, estimate.currency)} – {formatPrice(estimate.high_amount, estimate.currency)}
                  </p>
                </div>
                <div>
                  <span className="text-[var(--muted)]">Comparables analizados:</span>
                  <p className="font-semibold text-[var(--foreground)]">
                    {estimate.number_of_comparables} vehículos
                  </p>
                </div>
              </div>

              <p className="text-[0.75rem] text-[var(--muted)]">
                Calculado el {formatDate(estimate.calculated_at)} mediante mediana IQR de comparables homogéneos.
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center gap-3 py-6 text-center">
              <Calculator aria-hidden size={32} className="text-[var(--muted)]" />
              <p className="text-sm text-[var(--muted)]">
                Aún no se ha calculado la estimación de mercado para este vehículo.
              </p>
              <Button
                onClick={() => estimateMutation.mutate()}
                disabled={estimateMutation.isPending}
              >
                {estimateMutation.isPending ? "Calculando…" : "Calcular estimación ahora"}
              </Button>
            </div>
          )}
        </section>
      </div>

      {/* Histórico Consolidado */}
      {history && (
        <section
          aria-labelledby="vehicle-history-title"
          className="rounded-[var(--radius)] border border-[var(--border)] bg-white p-5 shadow-xs"
        >
          <h3 id="vehicle-history-title" className="mb-4 text-base font-bold text-[var(--foreground)]">
            Evolución e Histórico de Precios
          </h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 text-center">
            <div className="rounded-[var(--radius)] border border-[var(--border)] p-3">
              <span className="text-xs text-[var(--muted)]">Días en mercado</span>
              <p className="mt-1 text-xl font-bold text-[var(--foreground)] flex items-center justify-center gap-1">
                <Clock aria-hidden size={18} className="text-[var(--muted)]" />
                {history.days_on_market}
              </p>
            </div>
            <div className="rounded-[var(--radius)] border border-[var(--border)] p-3">
              <span className="text-xs text-[var(--muted)]">Mínimo observado</span>
              <p className="mt-1 text-xl font-bold text-[var(--success)]">
                {formatPrice(history.lowest_observed_price)}
              </p>
            </div>
            <div className="rounded-[var(--radius)] border border-[var(--border)] p-3">
              <span className="text-xs text-[var(--muted)]">Máximo observado</span>
              <p className="mt-1 text-xl font-bold text-[var(--foreground)]">
                {formatPrice(history.highest_observed_price)}
              </p>
            </div>
            <div className="rounded-[var(--radius)] border border-[var(--border)] p-3">
              <span className="text-xs text-[var(--muted)]">Cambios de precio</span>
              <p className="mt-1 text-xl font-bold text-[var(--foreground)] flex items-center justify-center gap-1">
                <Tag aria-hidden size={18} className="text-[var(--muted)]" />
                {history.total_price_changes}
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Anuncios vinculados */}
      <section
        aria-labelledby="linked-listings-title"
        className="rounded-[var(--radius)] border border-[var(--border)] bg-white p-5 shadow-xs"
      >
        <h3 id="linked-listings-title" className="mb-4 text-base font-bold text-[var(--foreground)]">
          Anuncios Enlazados ({vehicle.listings.length})
        </h3>
        {vehicle.listings.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">No hay anuncios vinculados a este vehículo.</p>
        ) : (
          <div className="flex flex-col divide-y divide-[var(--border)]">
            {vehicle.listings.map((l) => (
              <div key={l.id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-[var(--foreground)]">
                      {l.brand} {l.model} ({l.year})
                    </span>
                    <Badge tone={l.status === "ACTIVE" ? "success" : "neutral"}>
                      {STATUS_LABELS[l.status] ?? l.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-[var(--muted)]">
                    Ref: {l.external_id} {l.province ? `• ${l.province}` : ""} • {formatKm(l.mileage_km)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-base font-bold text-[var(--foreground)]">
                    {formatPrice(l.price_amount, l.price_currency)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
