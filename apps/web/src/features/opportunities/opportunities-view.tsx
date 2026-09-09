"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Filter,
  Loader2,
  RefreshCw,
  Search,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import type {
  OpportunityFilterParams,
  OpportunityPage,
  OpportunityRead,
  OpportunityStatus,
} from "@/features/opportunities/types";
import {
  getOpportunities,
  updateOpportunityStatus,
} from "@/features/opportunities/api";
import {
  OPPORTUNITY_STATUS_LABELS,
  formatEuros,
} from "@/features/opportunities/format";
import { OpportunityCard } from "@/features/opportunities/opportunity-card";

const STATUS_FILTER_OPTIONS: Array<{ value: OpportunityStatus | "ALL"; label: string }> = [
  { value: "ALL", label: "Todos los estados" },
  { value: "IDENTIFIED", label: "Identificadas" },
  { value: "ANALYZING", label: "En análisis" },
  { value: "VALIDATED", label: "Validadas" },
  { value: "DISCARDED", label: "Descartadas" },
  { value: "PURCHASED", label: "Compradas" },
  { value: "SOLD", label: "Vendidas" },
];

export function OpportunitiesView() {
  const [data, setData] = useState<OpportunityPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [statusFilter, setStatusFilter] = useState<OpportunityStatus | "ALL">("ALL");
  const [minScore, setMinScore] = useState<number | "">("");
  const [brandSearch, setBrandSearch] = useState("");
  const [page, setPage] = useState(1);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchOpportunities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: OpportunityFilterParams = {
        page,
        pageSize: 15,
        status: statusFilter === "ALL" ? undefined : statusFilter,
        min_score: minScore === "" ? undefined : Number(minScore),
        brand: brandSearch.trim() || undefined,
      };
      const res = await getOpportunities(params);
      setData(res);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Error al cargar las oportunidades de compra-venta.",
      );
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, minScore, brandSearch]);

  useEffect(() => {
    void fetchOpportunities();
  }, [fetchOpportunities]);

  const handleStatusChange = async (
    opportunityId: string,
    newStatus: OpportunityStatus,
  ) => {
    setUpdatingId(opportunityId);
    try {
      const updated = await updateOpportunityStatus(opportunityId, newStatus);
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          items: prev.items.map((item) =>
            item.id === opportunityId ? { ...item, status: updated.status } : item,
          ),
        };
      });
    } catch (err) {
      alert(
        err instanceof Error
          ? err.message
          : "No se pudo actualizar el estado de la oportunidad.",
      );
    } finally {
      setUpdatingId(null);
    }
  };

  const totalValidated = data?.items.filter((o) => o.status === "VALIDATED").length ?? 0;

  return (
    <div className="space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Cabecera y Resumen */}
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="text-[var(--accent)]" size={22} aria-hidden />
            <h1 className="font-display text-xl font-bold tracking-tight text-[var(--foreground)] sm:text-2xl">
              Mesa de Oportunidades y Scoring
            </h1>
          </div>
          <p className="mt-1 text-xs text-[var(--muted)] sm:text-sm">
            Detección sistemática de vehículos infravalorados con motor multicriterio explicable de 9 componentes.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void fetchOpportunities()}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-xs font-semibold text-[var(--foreground)] transition-colors hover:bg-[var(--surface-hover)] focus:outline-none"
          aria-label="Actualizar listado de oportunidades"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} aria-hidden />
          <span>Actualizar</span>
        </button>
      </header>

      {/* KPI Cards Rápidas */}
      <section
        aria-label="Indicadores clave"
        className="grid grid-cols-1 gap-3 sm:grid-cols-3"
      >
        <div className="rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] p-4">
          <span className="text-xs text-[var(--muted)]">Oportunidades en Vista</span>
          <p className="mt-1 font-mono text-xl font-bold text-[var(--foreground)]">
            {data?.total ?? 0}
          </p>
        </div>
        <div className="rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] p-4">
          <span className="text-xs text-[var(--muted)]">Validadas en esta página</span>
          <p className="mt-1 font-mono text-xl font-bold text-emerald-600 dark:text-emerald-400">
            {totalValidated}
          </p>
        </div>
        <div className="rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] p-4">
          <span className="text-xs text-[var(--muted)]">Estrategia de Scoring Activa</span>
          <p className="mt-1 text-sm font-bold text-[var(--foreground)] truncate">
            Oportunidad Reventa Rápida (v1)
          </p>
        </div>
      </section>

      {/* Filtros */}
      <section
        aria-label="Filtros de búsqueda"
        className="flex flex-wrap items-center gap-3 rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] p-4 text-xs"
      >
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-[var(--muted)]" aria-hidden />
          <span className="font-semibold text-[var(--foreground)]">Filtrar:</span>
        </div>

        {/* Estado */}
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value as OpportunityStatus | "ALL");
            setPage(1);
          }}
          aria-label="Filtrar por estado"
          className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2.5 py-1.5 font-medium text-[var(--foreground)] focus:border-[var(--accent)] focus:outline-none"
        >
          {STATUS_FILTER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Score Mínimo */}
        <div className="flex items-center gap-1.5">
          <label htmlFor="min-score-input" className="text-[var(--muted)]">
            Score mín:
          </label>
          <input
            id="min-score-input"
            type="number"
            min={0}
            max={100}
            placeholder="Ej. 65"
            value={minScore}
            onChange={(e) => {
              setMinScore(e.target.value ? Number(e.target.value) : "");
              setPage(1);
            }}
            className="w-20 rounded-md border border-[var(--border)] bg-[var(--background)] px-2.5 py-1.5 text-center font-mono text-[var(--foreground)] focus:border-[var(--accent)] focus:outline-none"
          />
        </div>

        {/* Marca */}
        <div className="flex items-center gap-1.5">
          <label htmlFor="brand-search-input" className="text-[var(--muted)]">
            Marca:
          </label>
          <div className="relative">
            <input
              id="brand-search-input"
              type="text"
              placeholder="Ej. SEAT, BMW..."
              value={brandSearch}
              onChange={(e) => {
                setBrandSearch(e.target.value);
                setPage(1);
              }}
              className="w-36 rounded-md border border-[var(--border)] bg-[var(--background)] py-1.5 pl-2.5 pr-7 text-[var(--foreground)] placeholder:text-[var(--muted-soft)] focus:border-[var(--accent)] focus:outline-none"
            />
            <Search
              size={12}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--muted)] pointer-events-none"
              aria-hidden
            />
          </div>
        </div>
      </section>

      {/* Estados de carga / error / lista */}
      {loading && !data && (
        <div
          role="status"
          aria-live="polite"
          className="flex min-h-64 flex-col items-center justify-center gap-2 rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] p-8 text-center text-sm text-[var(--muted)]"
        >
          <Loader2 className="animate-spin text-[var(--accent)]" size={28} />
          <p>Calculando y cargando oportunidades de mercado...</p>
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="flex items-center gap-2.5 rounded-[var(--radius-card)] border border-rose-500/30 bg-rose-500/10 p-4 text-xs font-semibold text-rose-600 dark:text-rose-400"
        >
          <AlertCircle size={18} aria-hidden />
          <p>{error}</p>
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="flex min-h-64 flex-col items-center justify-center gap-2 rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface)] p-8 text-center text-sm text-[var(--muted)]">
          <Sparkles size={32} className="opacity-40" aria-hidden />
          <p className="font-semibold text-[var(--foreground)]">
            No se han encontrado oportunidades
          </p>
          <p className="text-xs text-[var(--muted-soft)] max-w-sm">
            Prueba a reducir los filtros de score o cambiar el estado para ver más unidades evaluadas.
          </p>
        </div>
      )}

      {/* Lista de Oportunidades */}
      {data && data.items.length > 0 && (
        <section aria-label="Lista de oportunidades" className="space-y-4">
          {data.items.map((opp) => (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              onStatusChange={handleStatusChange}
              isUpdatingStatus={updatingId === opp.id}
            />
          ))}

          {/* Paginación */}
          <div className="flex items-center justify-between border-t border-[var(--border)] pt-4 text-xs">
            <span className="text-[var(--muted)]">
              Página {data.page} de {Math.max(1, Math.ceil(data.total / data.page_size))} ({data.total} oportunidades)
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1 || loading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 font-semibold text-[var(--foreground)] disabled:opacity-50 hover:bg-[var(--surface-hover)]"
              >
                Anterior
              </button>
              <button
                type="button"
                disabled={!data.has_more || loading}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 font-semibold text-[var(--foreground)] disabled:opacity-50 hover:bg-[var(--surface-hover)]"
              >
                Siguiente
              </button>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
