"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { getListings, syncSource } from "@/features/listings/api";
import { FilterForm } from "@/features/listings/filter-form";
import { ListingCard } from "@/features/listings/listing-card";
import { ListingDetailPanel } from "@/features/listings/listing-detail";
import { ManualListingForm } from "@/features/listings/manual-listing-form";
import type { ListingFilters } from "@/features/listings/types";
import { ApiError } from "@/lib/api";

type Mode = { name: "list" } | { name: "detail"; id: string } | { name: "manual" };

const PAGE_SIZE = 12;

export function ListingsView() {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<Mode>({ name: "list" });
  const [filters, setFilters] = useState<ListingFilters>({ sort: "newest" });
  const [page, setPage] = useState(1);
  const [syncMessage, setSyncMessage] = useState<string>();

  const query = useQuery({
    queryKey: ["listings", filters, page],
    queryFn: () => getListings({ ...filters, page, page_size: PAGE_SIZE }),
  });

  const sync = useMutation({
    mutationFn: () => syncSource("mock"),
    onSuccess: (run) => {
      setSyncMessage(
        `Sincronización ${run.status === "SUCCESS" ? "completada" : run.status.toLowerCase()}: ` +
          `${run.listings_created} nuevos, ${run.listings_updated} actualizados.`,
      );
      queryClient.invalidateQueries({ queryKey: ["listings"] });
    },
    onError: (error) => {
      setSyncMessage(
        error instanceof ApiError
          ? "No se pudo sincronizar el catálogo Mock."
          : "Error inesperado al sincronizar.",
      );
    },
  });

  function applyFilters(next: ListingFilters) {
    setFilters(next);
    setPage(1);
  }

  if (mode.name === "detail") {
    return (
      <ListingDetailPanel
        listingId={mode.id}
        onBack={() => setMode({ name: "list" })}
      />
    );
  }

  if (mode.name === "manual") {
    return (
      <section className="mx-auto max-w-3xl px-6 py-10 sm:px-10">
        <h1 className="text-[1.75rem] leading-9 font-semibold tracking-[-0.025em]">
          Registrar vehículo
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Anota una ficha observada en el mercado. No se descarga contenido de
          terceros.
        </p>
        <div className="mt-6">
          <ManualListingForm
            onCreated={() => setMode({ name: "list" })}
            onCancel={() => setMode({ name: "list" })}
          />
        </div>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-6xl px-6 py-10 sm:px-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-[1.75rem] leading-9 font-semibold tracking-[-0.025em]">
          Anuncios
        </h1>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="min-h-11 rounded-[var(--radius)] border border-[var(--border)] px-4 text-sm font-medium hover:border-[#aeb3b7] disabled:opacity-60"
            onClick={() => sync.mutate()}
            disabled={sync.isPending}
          >
            {sync.isPending ? "Sincronizando…" : "Sincronizar catálogo Mock"}
          </button>
          <Button type="button" onClick={() => setMode({ name: "manual" })}>
            Registrar vehículo
          </Button>
        </div>
      </div>

      {syncMessage ? (
        <p className="mt-4 text-sm text-[var(--muted)]" role="status">
          {syncMessage}
        </p>
      ) : null}

      <div className="mt-6 rounded-[var(--radius)] border border-[var(--border)] p-4">
        <FilterForm onApply={applyFilters} />
      </div>

      <div className="mt-6">
        {query.isPending ? (
          <p className="text-sm text-[var(--muted)]" aria-busy="true">
            Cargando anuncios…
          </p>
        ) : query.isError ? (
          <p className="text-sm text-[var(--danger)]" role="alert">
            No se pudieron cargar los anuncios.
          </p>
        ) : query.data.items.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">
            No hay anuncios que coincidan. Sincroniza el catálogo Mock o ajusta
            los filtros.
          </p>
        ) : (
          <>
            <p className="text-sm text-[var(--muted)]">
              {query.data.total} anuncios · página {query.data.page}
            </p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {query.data.items.map((listing) => (
                <ListingCard
                  key={listing.id}
                  listing={listing}
                  onOpen={(id) => setMode({ name: "detail", id })}
                />
              ))}
            </div>
            <div className="mt-6 flex items-center gap-3">
              <button
                type="button"
                className="min-h-11 px-3 text-sm disabled:opacity-40"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Anterior
              </button>
              <button
                type="button"
                className="min-h-11 px-3 text-sm disabled:opacity-40"
                onClick={() => setPage((p) => p + 1)}
                disabled={!query.data.has_more}
              >
                Siguiente
              </button>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
