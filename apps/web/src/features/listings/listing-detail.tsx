"use client";

import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowUpRight,
  CalendarDays,
  Fuel,
  Gauge,
  MapPin,
  Store,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { getListing } from "@/features/listings/api";
import {
  FUEL_LABELS,
  SELLER_LABELS,
  STATUS_LABELS,
  TRANSMISSION_LABELS,
  formatDate,
  formatKm,
  formatPrice,
} from "@/features/listings/format";

type ListingDetailProps = {
  listingId: string;
  onBack: () => void;
};

export function ListingDetailPanel({ listingId, onBack }: ListingDetailProps) {
  const detail = useQuery({
    queryKey: ["listing", listingId],
    queryFn: () => getListing(listingId),
  });

  return (
    <section className="page-frame max-w-6xl">
      <Button variant="ghost" className="-ml-3" onClick={onBack}>
        <ArrowLeft aria-hidden size={17} />
        Volver a la lista
      </Button>

      {detail.isPending ? (
        <div className="mt-8 h-80 animate-pulse rounded-[var(--radius-card)] bg-[var(--surface-inset)]">
          <p className="sr-only" aria-busy="true">
            Cargando anuncio…
          </p>
        </div>
      ) : detail.isError ? (
        <div className="empty-state mt-8 text-[var(--danger)]" role="alert">
          <p className="font-semibold">No se pudo cargar el anuncio.</p>
          <Button variant="secondary" onClick={() => void detail.refetch()}>
            Reintentar
          </Button>
        </div>
      ) : (
        <article className="mt-5">
          <header className="overflow-hidden rounded-[var(--radius-panel)] bg-[var(--foreground)] p-5 text-white shadow-[var(--shadow-raised)] sm:p-7">
            <div className="flex flex-col gap-7 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <div className="flex items-center gap-2 text-[#9bd2c3]">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#9bd2c3]" />
                  <p className="text-[0.6875rem] font-bold tracking-[0.11em] uppercase">
                    Unidad en mercado
                  </p>
                </div>
                <h1 className="font-display mt-3 text-3xl leading-none font-semibold tracking-[-0.04em] sm:text-4xl">
                  {detail.data.brand} {detail.data.model}
                </h1>
                <p className="mt-2 text-sm text-white/60">
                  {detail.data.trim ?? "Versión sin especificar"} ·{" "}
                  {detail.data.year}
                </p>
              </div>
              <div className="sm:text-right">
                <p className="text-[0.6875rem] font-bold tracking-[0.11em] text-white/45 uppercase">
                  Precio anunciado
                </p>
                <p className="font-data mt-1 text-4xl leading-none font-semibold tracking-[-0.045em]">
                  {formatPrice(
                    detail.data.price_amount,
                    detail.data.price_currency,
                  )}
                </p>
              </div>
            </div>
          </header>

          <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1.4fr)_minmax(18rem,0.8fr)]">
            <section
              className="workbench-panel p-5 sm:p-6"
              aria-labelledby="listing-data-title"
            >
              <p className="eyebrow">Lectura rápida</p>
              <h2 id="listing-data-title" className="section-title mt-1">
                Datos del anuncio
              </h2>
              <dl className="mt-5 grid gap-px overflow-hidden rounded-[var(--radius-control)] bg-[var(--border)] sm:grid-cols-2">
                {[
                  {
                    icon: Gauge,
                    term: "Kilometraje",
                    value: formatKm(detail.data.mileage_km),
                  },
                  {
                    icon: Fuel,
                    term: "Combustible",
                    value: FUEL_LABELS[detail.data.fuel_type],
                  },
                  {
                    icon: CalendarDays,
                    term: "Cambio",
                    value: TRANSMISSION_LABELS[detail.data.transmission],
                  },
                  {
                    icon: Store,
                    term: "Vendedor",
                    value: SELLER_LABELS[detail.data.seller_type],
                  },
                  {
                    icon: MapPin,
                    term: "Provincia",
                    value: detail.data.province ?? "—",
                  },
                  {
                    icon: CalendarDays,
                    term: "Estado",
                    value: STATUS_LABELS[detail.data.status],
                  },
                ].map(({ icon: Icon, term, value }) => (
                  <div key={term} className="bg-[var(--surface-inset)] p-4">
                    <dt className="flex items-center gap-1.5 text-[0.6875rem] font-semibold text-[var(--muted)]">
                      <Icon aria-hidden size={14} />
                      {term}
                    </dt>
                    <dd className="font-data mt-1 text-sm font-semibold">
                      {value}
                    </dd>
                  </div>
                ))}
              </dl>

              {detail.data.description ? (
                <div className="mt-6 border-t border-[var(--border)] pt-5">
                  <h2 className="section-title">Observaciones</h2>
                  <p className="mt-2 text-sm leading-6 whitespace-pre-line text-[var(--foreground-secondary)]">
                    {detail.data.description}
                  </p>
                </div>
              ) : null}

              {detail.data.url ? (
                <a
                  className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-control)] bg-[var(--foreground)] px-4 text-sm font-semibold text-white transition-colors hover:bg-[var(--accent)]"
                  href={detail.data.url}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  Ver anuncio original
                  <ArrowUpRight aria-hidden size={16} />
                </a>
              ) : null}
            </section>

            <section
              className="workbench-panel self-start overflow-hidden"
              aria-labelledby="listing-history-title"
            >
              <div className="border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4">
                <p className="eyebrow">Seguimiento</p>
                <h2 id="listing-history-title" className="section-title mt-1">
                  Histórico de observaciones
                </h2>
              </div>
              <ul className="divide-y divide-[var(--border)] px-5">
                {detail.data.snapshots.map((snapshot) => (
                  <li
                    key={snapshot.observed_at}
                    className="flex items-center justify-between gap-4 py-4"
                  >
                    <span className="text-xs text-[var(--muted)]">
                      {formatDate(snapshot.observed_at)}
                    </span>
                    <span className="text-right">
                      <span className="font-data block text-sm font-semibold">
                        {formatPrice(
                          snapshot.price_amount,
                          snapshot.price_currency,
                        )}
                      </span>
                      <span className="font-data block text-xs text-[var(--muted)]">
                        {formatKm(snapshot.mileage_km)}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </article>
      )}
    </section>
  );
}
