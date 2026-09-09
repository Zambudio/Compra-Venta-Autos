"use client";

import { ArrowUpRight, CalendarDays, Fuel, Gauge, MapPin } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  FUEL_LABELS,
  SELLER_LABELS,
  formatKm,
  formatPrice,
} from "@/features/listings/format";
import type { Listing } from "@/features/listings/types";

type ListingCardProps = {
  listing: Listing;
  onOpen: (id: string) => void;
};

export function ListingCard({ listing, onOpen }: ListingCardProps) {
  return (
    <article className="group flex min-h-full flex-col overflow-hidden rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface-raised)] shadow-[var(--shadow-card)] transition-[border-color,box-shadow,transform] duration-200 ease-[cubic-bezier(0.23,1,0.32,1)] hover:-translate-y-0.5 hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-raised)]">
      <div className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span
            className={`h-1.5 w-1.5 rounded-full ${listing.status === "ACTIVE" ? "bg-[var(--success)]" : "bg-[var(--muted-soft)]"}`}
            aria-hidden
          />
          <span className="text-[0.6875rem] font-bold tracking-[0.08em] text-[var(--muted)] uppercase">
            {listing.status === "ACTIVE" ? "En mercado" : "Sin verificar"}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Badge
            tone={listing.seller_type === "DEALER" ? "warning" : "neutral"}
          >
            {SELLER_LABELS[listing.seller_type]}
          </Badge>
          <Badge>{listing.source_key === "manual" ? "Manual" : "Mock"}</Badge>
        </div>
      </div>

      <div className="flex flex-1 flex-col p-4 sm:p-5">
        <div className="flex items-start justify-between gap-5">
          <div className="min-w-0">
            <p className="eyebrow">Unidad observada</p>
            <h2 className="font-display mt-1 text-xl leading-tight font-semibold tracking-[-0.025em] text-balance">
              {listing.brand} {listing.model}
            </h2>
            <p className="mt-1 truncate text-sm text-[var(--muted)]">
              {listing.trim ?? "Versión sin especificar"}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <p className="eyebrow">Precio</p>
            <p className="font-data mt-0.5 text-2xl leading-none font-semibold tracking-[-0.035em]">
              {formatPrice(listing.price_amount, listing.price_currency)}
            </p>
          </div>
        </div>

        <dl className="mt-5 grid grid-cols-3 divide-x divide-[var(--border)] rounded-[var(--radius-control)] bg-[var(--surface-inset)] py-3">
          <div className="px-3 first:pl-0 sm:first:pl-3">
            <dt className="flex items-center gap-1 text-[0.625rem] font-bold tracking-[0.08em] text-[var(--muted)] uppercase">
              <CalendarDays aria-hidden size={12} />
              Año
            </dt>
            <dd className="font-data mt-1 text-sm font-semibold">
              {listing.year}
            </dd>
          </div>
          <div className="px-3">
            <dt className="flex items-center gap-1 text-[0.625rem] font-bold tracking-[0.08em] text-[var(--muted)] uppercase">
              <Gauge aria-hidden size={12} />
              Kilómetros
            </dt>
            <dd className="font-data mt-1 text-sm font-semibold">
              {formatKm(listing.mileage_km)}
            </dd>
          </div>
          <div className="min-w-0 px-3">
            <dt className="flex items-center gap-1 text-[0.625rem] font-bold tracking-[0.08em] text-[var(--muted)] uppercase">
              <Fuel aria-hidden size={12} />
              Motor
            </dt>
            <dd className="mt-1 truncate text-sm font-semibold">
              {FUEL_LABELS[listing.fuel_type]}
            </dd>
          </div>
        </dl>

        <div className="mt-4 flex min-h-6 items-center gap-1.5 text-xs text-[var(--muted)]">
          <MapPin aria-hidden size={14} />
          {listing.province ?? "Ubicación no indicada"}
        </div>

        <div className="mt-auto flex items-center gap-2 border-t border-[var(--border)] pt-4">
          <button
            type="button"
            aria-label="Ver detalle"
            className="inline-flex min-h-11 flex-1 items-center justify-center rounded-[var(--radius-control)] bg-[var(--foreground)] px-4 text-sm font-semibold text-white transition-[background-color,transform] duration-150 hover:bg-[var(--accent)] active:scale-[0.98]"
            onClick={() => onOpen(listing.id)}
          >
            Analizar ficha
          </button>
          {listing.url ? (
            <a
              className="grid h-11 w-11 shrink-0 place-items-center rounded-[var(--radius-control)] border border-[var(--border-strong)] text-[var(--muted)] transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
              href={listing.url}
              target="_blank"
              rel="noreferrer noopener"
              aria-label="Ver anuncio original"
            >
              <ArrowUpRight aria-hidden size={18} />
            </a>
          ) : null}
        </div>
      </div>
    </article>
  );
}
