"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { RefreshCw, CarFront, CheckCircle2 } from "lucide-react";

import { getWatchlist } from "@/features/watchlist/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { InspectionPanel } from "./inspection-panel";

export function WatchlistView() {
  const [activeEntryId, setActiveEntryId] = useState<string | null>(null);

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ["watchlist"],
    queryFn: () => getWatchlist(true),
  });

  const activeEntry = data?.find((e) => e.id === activeEntryId);

  return (
    <div className="flex h-[calc(100dvh-4rem)] flex-col lg:h-dvh">
      <header className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--background)] px-4 py-4 lg:px-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Inspecciones & Watchlist</h1>
          <p className="text-sm text-[var(--muted)]">
            Coches bajo vigilancia y revisiones mecÃ¡nicas
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="icon"
            onClick={() => void refetch()}
            disabled={isRefetching}
            aria-label="Refrescar"
          >
            <RefreshCw size={18} className={isRefetching ? "animate-spin" : ""} />
          </Button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Lista de Watchlist */}
        <div className={`flex flex-1 flex-col overflow-y-auto p-4 lg:w-1/3 lg:flex-none lg:border-r lg:border-[var(--border)] ${activeEntryId ? "hidden lg:flex" : "flex"}`}>
          {isLoading ? (
            <div className="flex flex-1 items-center justify-center text-[var(--muted)]">
              Cargando watchlist...
            </div>
          ) : data?.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center text-center">
              <CarFront size={48} className="mb-4 text-[var(--muted-soft)]" strokeWidth={1} />
              <p className="font-semibold text-[var(--foreground)]">Watchlist vacÃ­a</p>
              <p className="text-sm text-[var(--muted)]">
                AÃ±ade oportunidades a tu watchlist para iniciar inspecciones.
              </p>
            </div>
          ) : (
            <ul className="flex flex-col gap-3">
              {data?.map((entry) => (
                <li key={entry.id}>
                  <button
                    onClick={() => setActiveEntryId(entry.id)}
                    className={`w-full rounded-[var(--radius-card)] border p-4 text-left transition-colors ${
                      activeEntryId === entry.id
                        ? "border-[var(--accent)] bg-[var(--accent-soft)]"
                        : "border-[var(--border)] bg-[var(--surface)] hover:border-[var(--border-strong)]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-semibold text-[var(--foreground)] truncate">
                        {entry.opportunity.title || "VehÃ­culo sin tÃ­tulo"}
                      </h3>
                      <Badge tone="neutral" className="shrink-0 bg-[var(--background)]">
                        {entry.opportunity.asking_price} â‚¬
                      </Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-[var(--muted)]">
                      <span>{entry.opportunity.year}</span>
                      <span>&bull;</span>
                      <span>{entry.opportunity.mileage_km?.toLocaleString()} km</span>
                      <span>&bull;</span>
                      <span>{entry.opportunity.city || "Sin ubicaciÃ³n"}</span>
                    </div>
                    {entry.notes && (
                      <p className="mt-3 text-sm text-[var(--muted)] line-clamp-2">
                        {entry.notes}
                      </p>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Panel principal de inspecciÃ³n */}
        <div className={`flex flex-1 flex-col overflow-hidden bg-[var(--surface)] ${!activeEntryId ? "hidden lg:flex" : "flex"}`}>
          {activeEntry ? (
            <InspectionPanel
              entry={activeEntry}
              onBack={() => setActiveEntryId(null)}
            />
          ) : (
            <div className="flex flex-1 items-center justify-center text-center text-[var(--muted)]">
              <div className="flex flex-col items-center gap-2">
                <CheckCircle2 size={48} className="text-[var(--border-strong)]" strokeWidth={1} />
                <p>Selecciona un vehÃ­culo para ver sus inspecciones</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
