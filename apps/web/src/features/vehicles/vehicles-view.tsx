"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CarFront,
  ChevronLeft,
  ChevronRight,
  GitMerge,
  Layers3,
  Search,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getMatchCandidates, getVehicles } from "@/features/vehicles/api";
import { MatchCandidatesView } from "@/features/vehicles/match-candidates-view";
import { VehicleCard } from "@/features/vehicles/vehicle-card";
import { VehicleDetail } from "@/features/vehicles/vehicle-detail";

type SubTab = "catalog" | "candidates";

export function VehiclesView() {
  const [activeTab, setActiveTab] = useState<SubTab>("catalog");
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>(
    null,
  );
  const [brandFilter, setBrandFilter] = useState("");
  const [modelFilter, setModelFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data: candidatesData } = useQuery({
    queryKey: ["match-candidates", "PENDING"],
    queryFn: () => getMatchCandidates("PENDING", 1, 1),
  });

  const pendingCount = candidatesData?.total ?? 0;

  const {
    data: vehiclesData,
    isLoading,
    isError,
    error,
  } = useQuery({
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
      <div className="page-frame">
        <VehicleDetail
          vehicleId={selectedVehicleId}
          onBack={() => setSelectedVehicleId(null)}
        />
      </div>
    );
  }

  return (
    <div className="page-frame">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="eyebrow">Inventario / Identidad</p>
          <h1 className="page-title mt-1">Vehículos y Mercado</h1>
          <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
            Reúne anuncios del mismo vehículo, valida coincidencias y analiza
            cada unidad como una única oportunidad.
          </p>
        </div>

        <nav
          aria-label="Subsecciones de vehículos"
          className="inline-flex self-start rounded-[0.625rem] bg-[var(--surface-inset)] p-1"
        >
          <button
            type="button"
            onClick={() => setActiveTab("catalog")}
            aria-current={activeTab === "catalog" ? "true" : undefined}
            className={`inline-flex min-h-10 items-center gap-2 rounded-[var(--radius-control)] px-3.5 text-xs font-semibold transition-[background-color,color,box-shadow] ${activeTab === "catalog" ? "bg-[var(--surface-raised)] text-[var(--foreground)] shadow-sm" : "text-[var(--muted)] hover:text-[var(--foreground)]"}`}
          >
            <Layers3 aria-hidden size={16} />
            Catálogo Unificado
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("candidates")}
            aria-current={activeTab === "candidates" ? "true" : undefined}
            className={`inline-flex min-h-10 items-center gap-2 rounded-[var(--radius-control)] px-3.5 text-xs font-semibold transition-[background-color,color,box-shadow] ${activeTab === "candidates" ? "bg-[var(--surface-raised)] text-[var(--foreground)] shadow-sm" : "text-[var(--muted)] hover:text-[var(--foreground)]"}`}
          >
            <GitMerge aria-hidden size={16} />
            Deduplicación
            {pendingCount > 0 ? (
              <Badge tone="warning">{pendingCount}</Badge>
            ) : null}
          </button>
        </nav>
      </div>

      {activeTab === "candidates" ? (
        <div className="mt-8">
          <MatchCandidatesView />
        </div>
      ) : (
        <div className="mt-8 flex flex-col gap-7">
          <section
            aria-labelledby="vehicles-search-heading"
            className="workbench-panel flex flex-col gap-4 p-4 sm:flex-row sm:items-end sm:p-5"
          >
            <div className="flex items-center gap-3 sm:self-center">
              <span className="grid h-9 w-9 place-items-center rounded-[var(--radius-control)] bg-[var(--accent-soft)] text-[var(--accent)]">
                <Search aria-hidden size={17} />
              </span>
              <div>
                <h2 id="vehicles-search-heading" className="section-title">
                  Buscar unidad
                </h2>
                <p className="text-xs text-[var(--muted)]">
                  Marca y modelo canónicos
                </p>
              </div>
            </div>
            <div className="min-w-[12rem] flex-1">
              <label
                htmlFor="vehicle-brand-filter"
                className="mb-1.5 block text-xs font-semibold text-[var(--foreground-secondary)]"
              >
                Marca
              </label>
              <Input
                id="vehicle-brand-filter"
                type="search"
                placeholder="SEAT, Volkswagen…"
                value={brandFilter}
                onChange={(event) => {
                  setBrandFilter(event.target.value);
                  setPage(1);
                }}
              />
            </div>
            <div className="min-w-[12rem] flex-1">
              <label
                htmlFor="vehicle-model-filter"
                className="mb-1.5 block text-xs font-semibold text-[var(--foreground-secondary)]"
              >
                Modelo
              </label>
              <Input
                id="vehicle-model-filter"
                type="search"
                placeholder="Ibiza, Golf…"
                value={modelFilter}
                onChange={(event) => {
                  setModelFilter(event.target.value);
                  setPage(1);
                }}
              />
            </div>
            {brandFilter || modelFilter ? (
              <Button
                variant="ghost"
                onClick={() => {
                  setBrandFilter("");
                  setModelFilter("");
                  setPage(1);
                }}
              >
                Limpiar
              </Button>
            ) : null}
          </section>

          {isLoading ? (
            <div
              className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
              aria-live="polite"
              aria-label="Cargando vehículos unificados"
            >
              {Array.from({ length: 6 }).map((_, index) => (
                <div
                  key={index}
                  className="h-80 animate-pulse rounded-[var(--radius-card)] bg-[var(--surface-inset)]"
                />
              ))}
            </div>
          ) : null}

          {isError ? (
            <div className="empty-state text-[var(--danger)]" role="alert">
              <p className="font-semibold">
                {error instanceof Error
                  ? error.message
                  : "Error al cargar la lista de vehículos."}
              </p>
            </div>
          ) : null}

          {!isLoading && !isError && vehiclesData?.items.length === 0 ? (
            <div className="empty-state">
              <CarFront aria-hidden size={38} className="text-[var(--muted)]" />
              <div>
                <h3 className="font-semibold">
                  No se encontraron vehículos unificados
                </h3>
                <p className="mt-1 max-w-md text-sm text-[var(--muted)]">
                  Confirma coincidencias entre anuncios en Deduplicación para
                  construir el inventario consolidado.
                </p>
              </div>
            </div>
          ) : null}

          {!isLoading &&
          !isError &&
          vehiclesData &&
          vehiclesData.items.length > 0 ? (
            <>
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="eyebrow">Inventario consolidado</p>
                  <p className="mt-0.5 text-sm font-semibold">
                    <span className="font-data">{vehiclesData.total}</span>{" "}
                    unidades identificadas
                  </p>
                </div>
                <p className="text-xs text-[var(--muted)]">
                  Página <span className="font-data">{page}</span>
                </p>
              </div>
              <div
                className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
                aria-label="Catálogo de vehículos"
              >
                {vehiclesData.items.map((vehicle) => (
                  <VehicleCard
                    key={vehicle.id}
                    vehicle={vehicle}
                    onSelect={(selected) => setSelectedVehicleId(selected.id)}
                  />
                ))}
              </div>
              <div className="flex items-center justify-between border-t border-[var(--border)] pt-5">
                <span className="text-xs text-[var(--muted)]">
                  Total: <span className="font-data">{vehiclesData.total}</span>{" "}
                  {vehiclesData.total === 1 ? "vehículo" : "vehículos"}
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="compact"
                    onClick={() =>
                      setPage((current) => Math.max(1, current - 1))
                    }
                    disabled={page === 1}
                  >
                    <ChevronLeft aria-hidden size={16} />
                    Anterior
                  </Button>
                  <Button
                    variant="secondary"
                    size="compact"
                    onClick={() => setPage((current) => current + 1)}
                    disabled={!vehiclesData.has_more}
                  >
                    Siguiente
                    <ChevronRight aria-hidden size={16} />
                  </Button>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}
