"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

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
    <section className="mx-auto max-w-3xl px-6 py-10 sm:px-10">
      <button
        type="button"
        className="mb-6 inline-flex min-h-11 items-center gap-2 text-sm text-[var(--muted)] hover:text-[var(--foreground)]"
        onClick={onBack}
      >
        <ArrowLeft aria-hidden size={17} />
        Volver a la lista
      </button>

      {detail.isPending ? (
        <p className="text-sm text-[var(--muted)]" aria-busy="true">
          Cargando anuncio…
        </p>
      ) : detail.isError ? (
        <p className="text-sm text-[var(--danger)]" role="alert">
          No se pudo cargar el anuncio.
        </p>
      ) : (
        <article>
          <h1 className="text-[1.75rem] leading-9 font-semibold tracking-[-0.025em]">
            {detail.data.brand} {detail.data.model}
          </h1>
          <p className="mt-1 text-[var(--muted)]">
            {detail.data.trim ?? "Sin versión"} · {detail.data.year}
          </p>
          <p className="mt-4 text-2xl font-bold">
            {formatPrice(detail.data.price_amount, detail.data.price_currency)}
          </p>

          <dl className="mt-6 grid gap-x-8 gap-y-3 border-t border-[var(--border)] pt-4 sm:grid-cols-2">
            {[
              ["Kilometraje", formatKm(detail.data.mileage_km)],
              ["Combustible", FUEL_LABELS[detail.data.fuel_type]],
              ["Cambio", TRANSMISSION_LABELS[detail.data.transmission]],
              ["Vendedor", SELLER_LABELS[detail.data.seller_type]],
              ["Provincia", detail.data.province ?? "—"],
              ["Estado", STATUS_LABELS[detail.data.status]],
            ].map(([term, value]) => (
              <div key={term} className="grid grid-cols-[10rem_1fr] gap-2">
                <dt className="text-[var(--muted)]">{term}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>

          {detail.data.description ? (
            <p className="mt-6 text-sm whitespace-pre-line">
              {detail.data.description}
            </p>
          ) : null}

          <h2 className="mt-8 text-base font-semibold">
            Histórico de observaciones
          </h2>
          <ul className="mt-3 border-t border-[var(--border)]">
            {detail.data.snapshots.map((snap) => (
              <li
                key={snap.observed_at}
                className="flex items-center justify-between border-b border-[var(--border)] py-2 text-sm"
              >
                <span className="text-[var(--muted)]">
                  {formatDate(snap.observed_at)}
                </span>
                <span>
                  {formatPrice(snap.price_amount, snap.price_currency)} ·{" "}
                  {formatKm(snap.mileage_km)}
                </span>
              </li>
            ))}
          </ul>

          {detail.data.url ? (
            <a
              className="mt-6 inline-block text-sm font-medium text-[var(--accent)] hover:text-[var(--accent-hover)]"
              href={detail.data.url}
              target="_blank"
              rel="noreferrer noopener"
            >
              Ver anuncio original
            </a>
          ) : null}
        </article>
      )}
    </section>
  );
}
