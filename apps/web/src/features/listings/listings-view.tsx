"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Inbox,
  Plus,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { getListings, syncSource } from "@/features/listings/api";
import { FilterForm } from "@/features/listings/filter-form";
import { ListingCard } from "@/features/listings/listing-card";
import { ListingDetailPanel } from "@/features/listings/listing-detail";
import { ManualListingForm } from "@/features/listings/manual-listing-form";
import type { ListingFilters } from "@/features/listings/types";
import { ApiError } from "@/lib/api";

type Mode =
  { name: "list" } | { name: "detail"; id: string } | { name: "manual" };

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
        `Sincronización ${run.status === "SUCCESS" ? "completada" : run.status.toLowerCase()}: ${run.listings_created} nuevos, ${run.listings_updated} actualizados.`,
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
      <section className="page-frame max-w-4xl">
        <p className="eyebrow">Captura manual</p>
        <h1 className="page-title mt-1">Registrar vehículo</h1>
        <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
          Incorpora una unidad observada sin descargar contenido de terceros.
          Los datos quedarán listos para seguimiento y comparación.
        </p>
        <div className="workbench-panel mt-7 p-5 sm:p-6">
          <ManualListingForm
            onCreated={() => setMode({ name: "list" })}
            onCancel={() => setMode({ name: "list" })}
          />
        </div>
      </section>
    );
  }

  return (
    <section className="page-frame">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Mercado / Captura</p>
          <h1 className="page-title mt-1">Anuncios</h1>
          <p className="mt-2 max-w-xl text-sm text-[var(--muted)]">
            Explora unidades, compara precios y abre una ficha para validar la
            oportunidad.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            type="button"
            onClick={() => sync.mutate()}
            disabled={sync.isPending}
          >
            <RefreshCw
              aria-hidden
              size={16}
              className={sync.isPending ? "animate-spin" : undefined}
            />
            {sync.isPending ? "Sincronizando…" : "Sincronizar catálogo Mock"}
          </Button>
          <Button type="button" onClick={() => setMode({ name: "manual" })}>
            <Plus aria-hidden size={17} />
            Registrar vehículo
          </Button>
        </div>
      </div>

      {syncMessage ? (
        <div
          className="mt-5 flex items-start gap-3 rounded-[var(--radius-control)] border border-[color-mix(in_srgb,var(--success)_18%,transparent)] bg-[var(--success-soft)] px-4 py-3 text-sm text-[var(--success)]"
          role="status"
        >
          <CheckCircle2 aria-hidden size={18} className="mt-0.5 shrink-0" />
          {syncMessage}
        </div>
      ) : null}

      <section
        className="workbench-panel mt-7 overflow-hidden"
        aria-labelledby="listing-filters-title"
      >
        <div className="flex items-center gap-3 border-b border-[var(--border)] bg-[var(--surface)] px-4 py-3 sm:px-5">
          <span className="grid h-8 w-8 place-items-center rounded-[var(--radius-control)] bg-[var(--accent-soft)] text-[var(--accent)]">
            <SlidersHorizontal aria-hidden size={16} />
          </span>
          <div>
            <h2 id="listing-filters-title" className="section-title">
              Afinar búsqueda
            </h2>
            <p className="text-xs text-[var(--muted)]">
              Define el perfil de compra que quieres revisar.
            </p>
          </div>
        </div>
        <div className="p-4 sm:p-5">
          <FilterForm onApply={applyFilters} />
        </div>
      </section>

      <div className="mt-8">
        {query.isPending ? (
          <div
            className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
            aria-busy="true"
            aria-label="Cargando anuncios"
          >
            <p className="sr-only">Cargando anuncios…</p>
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="h-72 animate-pulse rounded-[var(--radius-card)] bg-[var(--surface-inset)]"
              />
            ))}
          </div>
        ) : query.isError ? (
          <div className="empty-state text-[var(--danger)]" role="alert">
            <Inbox aria-hidden size={32} />
            <p className="font-semibold">No se pudieron cargar los anuncios.</p>
            <Button variant="secondary" onClick={() => void query.refetch()}>
              Reintentar
            </Button>
          </div>
        ) : query.data.items.length === 0 ? (
          <div className="empty-state">
            <Inbox aria-hidden size={34} className="text-[var(--muted)]" />
            <div>
              <p className="font-semibold">No hay anuncios que coincidan.</p>
              <p className="mt-1 max-w-md text-sm text-[var(--muted)]">
                Ajusta los filtros o sincroniza el catálogo para incorporar
                nuevas observaciones.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-4 flex items-end justify-between gap-4">
              <p className="sr-only">
                {query.data.total} anuncios · página {query.data.page}
              </p>
              <div>
                <p className="eyebrow">Resultado del radar</p>
                <p className="mt-0.5 text-sm font-semibold">
                  <span className="font-data">{query.data.total}</span>{" "}
                  oportunidades observadas
                </p>
              </div>
              <p className="text-xs text-[var(--muted)]">
                Página <span className="font-data">{query.data.page}</span>
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {query.data.items.map((listing) => (
                <ListingCard
                  key={listing.id}
                  listing={listing}
                  onOpen={(id) => setMode({ name: "detail", id })}
                />
              ))}
            </div>
            <div className="mt-7 flex items-center justify-between border-t border-[var(--border)] pt-5">
              <p className="text-xs text-[var(--muted)]">
                Mostrando hasta {PAGE_SIZE} unidades por página
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="compact"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft aria-hidden size={16} />
                  Anterior
                </Button>
                <Button
                  variant="secondary"
                  size="compact"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!query.data.has_more}
                >
                  Siguiente
                  <ChevronRight aria-hidden size={16} />
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
