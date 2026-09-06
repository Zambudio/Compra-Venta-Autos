import { useQuery } from "@tanstack/react-query";
import { Car, Filter, GitMerge, Layers, Search } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getMatchCandidates, getVehicles } from "@/features/vehicles/api";
import { MatchCandidatesView } from "@/features/vehicles/match-candidates-view";
import { VehicleCard } from "@/features/vehicles/vehicle-card";
import { VehicleDetail } from "@/features/vehicles/vehicle-detail";
import type { Vehicle } from "@/features/vehicles/types";

type SubTab = "catalog" | "candidates";

export function VehiclesView() {
  const [activeTab, setActiveTab] = useState<SubTab>("catalog");
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>(null);
  const [brandFilter, setBrandFilter] = useState("");
  const [modelFilter, setModelFilter] = useState("");
  const [page, setPage] = useState(1);

  // Consulta de candidatos pendientes para mostrar el contador en el badge
  const { data: candidatesData } = useQuery({
    queryKey: ["match-candidates", "PENDING"],
    queryFn: () => getMatchCandidates("PENDING", 1, 1),
  });

  const pendingCount = candidatesData?.total ?? 0;

  // Consulta de vehículos
  const { data: vehiclesData, isLoading, isError, error } = useQuery({
    queryKey: ["vehicles", page, brandFilter, modelFilter],
    queryFn: () =>
      getVehicles({
        page,
        pageSize: 12,
        brand: brandFilter || undefined,
        model: modelFilter || undefined,
      }),
    enabled: activeTab === "catalog" && !selectedVehicleId,
  });

  if (selectedVehicleId) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-8 sm:px-10">
        <VehicleDetail
          vehicleId={selectedVehicleId}
          onBack={() => setSelectedVehicleId(null)}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-8 sm:px-10">
      {/* Navegación interna de la sección Vehículos */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div className="flex items-center gap-2">
          <Car aria-hidden size={24} className="text-[var(--accent)]" />
          <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
            Vehículos y Mercado
          </h1>
        </div>

        <nav aria-label="Subsecciones de vehículos" className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("catalog")}
            aria-current={activeTab === "catalog" ? "true" : undefined}
            className={`inline-flex min-h-10 items-center gap-2 rounded-[var(--radius)] px-4 text-sm font-medium transition-colors ${
              activeTab === "catalog"
                ? "bg-[var(--surface-hover)] text-[var(--foreground)]"
                : "text-[var(--muted)] hover:text-[var(--foreground)]"
            }`}
          >
            <Layers aria-hidden size={16} />
            Catálogo Unificado
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("candidates")}
            aria-current={activeTab === "candidates" ? "true" : undefined}
            className={`inline-flex min-h-10 items-center gap-2 rounded-[var(--radius)] px-4 text-sm font-medium transition-colors ${
              activeTab === "candidates"
                ? "bg-[var(--surface-hover)] text-[var(--foreground)]"
                : "text-[var(--muted)] hover:text-[var(--foreground)]"
            }`}
          >
            <GitMerge aria-hidden size={16} />
            Deduplicación
            {pendingCount > 0 && (
              <Badge tone="warning">
                {pendingCount}
              </Badge>
            )}
          </button>
        </nav>
      </div>

      {activeTab === "candidates" ? (
        <MatchCandidatesView />
      ) : (
        <div className="flex flex-col gap-6">
          {/* Filtros de búsqueda */}
          <section
            aria-labelledby="vehicles-search-heading"
            className="flex flex-wrap items-end gap-3 rounded-[var(--radius)] border border-[var(--border)] bg-white p-4 shadow-xs"
          >
            <h2 id="vehicles-search-heading" className="sr-only">
              Búsqueda de vehículos unificados
            </h2>
            <div className="flex-1 min-w-[200px]">
              <label htmlFor="vehicle-brand-filter" className="mb-1 block text-xs font-semibold text-[var(--foreground)]">
                Marca
              </label>
              <Input
                id="vehicle-brand-filter"
                type="search"
                placeholder="Ej. SEAT, Volkswagen…"
                value={brandFilter}
                onChange={(e) => {
                  setBrandFilter(e.target.value);
                  setPage(1);
                }}
              />
            </div>
            <div className="flex-1 min-w-[200px]">
              <label htmlFor="vehicle-model-filter" className="mb-1 block text-xs font-semibold text-[var(--foreground)]">
                Modelo
              </label>
              <Input
                id="vehicle-model-filter"
                type="search"
                placeholder="Ej. Ibiza, Golf…"
                value={modelFilter}
                onChange={(e) => {
                  setModelFilter(e.target.value);
                  setPage(1);
                }}
              />
            </div>
            {(brandFilter || modelFilter) && (
              <button
                type="button"
                onClick={() => {
                  setBrandFilter("");
                  setModelFilter("");
                  setPage(1);
                }}
                className="min-h-10 px-3 text-xs font-medium text-[var(--muted)] hover:text-[var(--foreground)]"
              >
                Limpiar filtros
              </button>
            )}
          </section>

          {/* Estado de carga */}
          {isLoading && (
            <div className="flex min-h-[250px] items-center justify-center" aria-live="polite">
              <p className="text-sm text-[var(--muted)]">Cargando vehículos unificados…</p>
            </div>
          )}

          {/* Error */}
          {isError && (
            <div className="p-4" role="alert">
              <p className="text-sm font-medium text-[var(--danger)]">
                {error instanceof Error ? error.message : "Error al cargar la lista de vehículos."}
              </p>
            </div>
          )}

          {/* Catálogo vacío */}
          {!isLoading && !isError && vehiclesData?.items.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 rounded-[var(--radius)] border border-[var(--border)] bg-white p-12 text-center">
              <Car aria-hidden size={40} className="text-[var(--muted)]" />
              <h3 className="text-base font-bold text-[var(--foreground)]">
                No se encontraron vehículos unificados
              </h3>
              <p className="max-w-md text-sm text-[var(--muted)]">
                Los vehículos se generan al confirmar coincidencias entre anuncios duplicados en la sección de Deduplicación.
              </p>
            </div>
          )}

          {/* Grid de vehículos */}
          {!isLoading && !isError && vehiclesData && vehiclesData.items.length > 0 && (
            <>
              <div
                className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
                aria-label="Catálogo de vehículos"
              >
                {vehiclesData.items.map((vehicle) => (
                  <VehicleCard
                    key={vehicle.id}
                    vehicle={vehicle}
                    onSelect={(v) => setSelectedVehicleId(v.id)}
                  />
                ))}
              </div>

              {/* Paginación */}
              <div className="flex items-center justify-between border-t border-[var(--border)] pt-4">
                <span className="text-xs text-[var(--muted)]">
                  Total: {vehiclesData.total} {vehiclesData.total === 1 ? "vehículo" : "vehículos"}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="min-h-9 rounded-[var(--radius)] border border-[var(--border)] px-3 text-xs font-medium disabled:opacity-50"
                  >
                    Anterior
                  </button>
                  <span className="text-xs text-[var(--muted)]">Página {page}</span>
                  <button
                    type="button"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!vehiclesData.has_more}
                    className="min-h-9 rounded-[var(--radius)] border border-[var(--border)] px-3 text-xs font-medium disabled:opacity-50"
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
