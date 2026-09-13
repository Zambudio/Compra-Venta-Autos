"use client";

import { useMutation } from "@tanstack/react-query";
import { ExternalLink, MapPin, Search, TriangleAlert } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { searchListings } from "@/features/listings/api";
import type { WallapopListing } from "@/features/listings/types";
import { ApiError } from "@/lib/api";

export function LiveListingSearch() {
  const [query, setQuery] = useState("");
  const search = useMutation({
    mutationFn: (value: string) => searchListings(value, {}),
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = query.trim();
    if (normalized.length >= 2) search.mutate(normalized);
  }

  const errorMessage =
    search.error instanceof ApiError && search.error.code === "source_disabled"
      ? "Activa Wallapop en Configuración para realizar búsquedas en tiempo real."
      : search.isError
        ? "Wallapop no está disponible ahora. Inténtalo de nuevo más tarde."
        : undefined;

  return (
    <section
      className="mt-7 overflow-hidden rounded-[var(--radius-card)] bg-[var(--foreground)] text-white shadow-[var(--shadow-card)]"
      aria-labelledby="live-search-title"
    >
      <div className="p-5 sm:p-6">
        <p className="text-[0.6875rem] font-bold tracking-[0.11em] text-white/50 uppercase">
          Radar en directo
        </p>
        <h2
          id="live-search-title"
          className="font-display mt-1 text-xl font-semibold"
        >
          Buscar anuncios reales en Wallapop
        </h2>
        <p className="mt-1 text-sm text-white/60">
          Consulta el mercado al momento; las búsquedas idénticas se reutilizan
          durante cinco minutos.
        </p>

        <form
          className="mt-5 flex flex-col gap-2 sm:flex-row"
          onSubmit={submit}
        >
          <label className="sr-only" htmlFor="wallapop-query">
            Buscar en Wallapop
          </label>
          <input
            id="wallapop-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            minLength={2}
            maxLength={120}
            required
            placeholder="BMW 320, SEAT Ibiza…"
            className="min-h-11 min-w-0 flex-1 rounded-[var(--radius-control)] border border-white/15 bg-white/10 px-4 text-sm text-white outline-none placeholder:text-white/35 focus:border-white/35 focus:ring-4 focus:ring-white/10"
          />
          <Button
            type="submit"
            aria-label="Buscar ahora"
            disabled={search.isPending || query.trim().length < 2}
            className="bg-[#83c8b6] text-[#10231f] hover:bg-[#9ad4c4]"
          >
            <Search aria-hidden size={17} />
            {search.isPending ? "Buscando…" : "Buscar ahora"}
          </Button>
        </form>

        {errorMessage ? (
          <div
            className="mt-4 flex items-start gap-2 text-sm text-[#ffc7c1]"
            role="alert"
          >
            <TriangleAlert aria-hidden size={18} className="mt-0.5 shrink-0" />
            {errorMessage}
          </div>
        ) : null}
      </div>

      {search.data ? (
        <div className="border-t border-white/10 bg-white text-[var(--foreground)]">
          <div className="flex items-center justify-between px-5 py-3 text-xs text-[var(--muted)]">
            <span>{search.data.total} resultados en Wallapop</span>
            <span>Consulta: {search.data.query}</span>
          </div>
          {search.data.listings.length === 0 ? (
            <p className="border-t border-[var(--border)] p-5 text-sm text-[var(--muted)]">
              No se encontraron anuncios para esta búsqueda.
            </p>
          ) : (
            <div className="divide-y divide-[var(--border)] border-t border-[var(--border)]">
              {search.data.listings.map((listing) => (
                <LiveResult key={listing.id} listing={listing} />
              ))}
            </div>
          )}
        </div>
      ) : null}
    </section>
  );
}

function LiveResult({ listing }: { listing: WallapopListing }) {
  return (
    <article className="grid gap-4 p-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
      <div className="min-w-0">
        <h3 className="truncate font-semibold">{listing.title}</h3>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--muted)]">
          {listing.location ? (
            <span className="inline-flex items-center gap-1">
              <MapPin aria-hidden size={13} />
              {listing.location}
            </span>
          ) : null}
          {listing.seller.name ? (
            <span>Vendedor: {listing.seller.name}</span>
          ) : null}
          {listing.seller.rating !== null ? (
            <span>Valoración: {listing.seller.rating}</span>
          ) : null}
        </div>
        {listing.description ? (
          <p className="mt-2 line-clamp-2 text-sm text-[var(--foreground-secondary)]">
            {listing.description}
          </p>
        ) : null}
      </div>
      <div className="flex items-center justify-between gap-4 sm:flex-col sm:items-end">
        <p className="font-data text-lg font-bold">
          {Number(listing.price).toLocaleString("es-ES")} €
        </p>
        <a
          href={listing.url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--accent)] underline-offset-4 hover:underline"
        >
          Abrir en Wallapop
          <ExternalLink aria-hidden size={13} />
        </a>
      </div>
    </article>
  );
}
