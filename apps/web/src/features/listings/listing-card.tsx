"use client";

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
    <article className="rounded-[var(--radius)] border border-[var(--border)] p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold">
            {listing.brand} {listing.model}
            {listing.trim ? (
              <span className="font-normal text-[var(--muted)]">
                {" "}
                · {listing.trim}
              </span>
            ) : null}
          </h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {listing.year} · {formatKm(listing.mileage_km)} ·{" "}
            {FUEL_LABELS[listing.fuel_type]}
            {listing.province ? ` · ${listing.province}` : ""}
          </p>
        </div>
        <p className="shrink-0 text-lg font-bold">
          {formatPrice(listing.price_amount, listing.price_currency)}
        </p>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Badge tone={listing.seller_type === "DEALER" ? "warning" : "neutral"}>
          {SELLER_LABELS[listing.seller_type]}
        </Badge>
        <Badge>{listing.source_key === "manual" ? "Manual" : "Mock"}</Badge>
      </div>

      <div className="mt-4 flex items-center gap-4 text-sm">
        <button
          type="button"
          className="min-h-11 font-medium text-[var(--accent)] hover:text-[var(--accent-hover)]"
          onClick={() => onOpen(listing.id)}
        >
          Ver detalle
        </button>
        {listing.url ? (
          <a
            className="min-h-11 text-[var(--muted)] hover:text-[var(--foreground)]"
            href={listing.url}
            target="_blank"
            rel="noreferrer noopener"
          >
            Ver anuncio original
          </a>
        ) : null}
      </div>
    </article>
  );
}
