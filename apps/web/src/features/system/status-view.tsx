"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, Database, Radio, Server, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { getSystemStatus } from "@/features/auth/api";

export function StatusView() {
  const status = useQuery({
    queryKey: ["system-status"],
    queryFn: getSystemStatus,
  });

  const rows = [
    {
      name: "API",
      description: "Servicios y contrato HTTP",
      value: status.data?.api === "available" ? "Disponible" : "Comprobando",
      icon: Server,
    },
    {
      name: "PostgreSQL",
      description: "Persistencia operativa",
      value:
        status.data?.postgresql === "available" ? "Disponible" : "Comprobando",
      icon: Database,
    },
    {
      name: "Redis",
      description: "Colas, caché y sesiones",
      value: status.data?.redis === "ready" ? "Preparado" : "Comprobando",
      icon: Radio,
    },
  ] as const;

  const readyCount = rows.filter(
    (row) => row.value === "Disponible" || row.value === "Preparado",
  ).length;

  return (
    <section className="page-frame max-w-5xl">
      <div>
        <p className="eyebrow">Operaciones / Infraestructura</p>
        <h1 className="page-title mt-1">Foundation operativa</h1>
        <p className="mt-2 max-w-xl text-sm text-[var(--muted)]">
          Estado en tiempo real de los servicios esenciales de MotorScope.
        </p>
      </div>

      {status.isError ? (
        <div
          className="mt-8 rounded-[var(--radius-card)] border border-[color-mix(in_srgb,var(--danger)_24%,transparent)] bg-[var(--danger-soft)] p-5 text-[var(--danger)]"
          role="alert"
        >
          <TriangleAlert aria-hidden size={22} />
          <p className="mt-3 font-semibold">
            No se pudo comprobar el estado del sistema.
          </p>
          <p className="mt-1 text-sm opacity-80">
            Revisa la conectividad con la API e inténtalo de nuevo.
          </p>
          <Button
            variant="secondary"
            size="compact"
            className="mt-4"
            onClick={() => void status.refetch()}
          >
            Reintentar
          </Button>
        </div>
      ) : (
        <>
          <div className="mt-8 overflow-hidden rounded-[var(--radius-card)] bg-[var(--foreground)] p-5 text-white shadow-[var(--shadow-card)] sm:p-6">
            <div className="flex items-start justify-between gap-6">
              <div>
                <p className="text-[0.6875rem] font-bold tracking-[0.11em] text-white/50 uppercase">
                  Estado global
                </p>
                <p className="font-display mt-2 text-2xl font-semibold tracking-[-0.025em]">
                  {status.isPending
                    ? "Verificando servicios"
                    : readyCount === rows.length
                      ? "Todo operativo"
                      : "Revisión en curso"}
                </p>
                <p className="mt-1 text-sm text-white/60">
                  {readyCount} de {rows.length} servicios respondiendo
                </p>
              </div>
              <span className="grid h-12 w-12 place-items-center rounded-full bg-white/8 ring-1 ring-white/10">
                <Activity
                  aria-hidden
                  size={22}
                  className={
                    readyCount === rows.length
                      ? "text-[#9ad4c4]"
                      : "text-white/45"
                  }
                />
              </span>
            </div>
            <div className="mt-6 h-1.5 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full origin-left rounded-full bg-[#83c8b6] transition-transform duration-300"
                style={{ transform: `scaleX(${readyCount / rows.length})` }}
              />
            </div>
          </div>

          <div className="workbench-panel mt-5 divide-y divide-[var(--border)] overflow-hidden">
            {rows.map(({ name, description, value, icon: Icon }) => {
              const isReady = value === "Disponible" || value === "Preparado";
              return (
                <div
                  key={name}
                  className="grid min-h-20 grid-cols-[auto_1fr_auto] items-center gap-4 px-4 sm:px-5"
                >
                  <span className="grid h-10 w-10 place-items-center rounded-[var(--radius-control)] bg-[var(--surface-inset)] text-[var(--muted)]">
                    <Icon aria-hidden size={18} />
                  </span>
                  <div>
                    <p className="font-semibold">{name}</p>
                    <p className="text-xs text-[var(--muted)]">{description}</p>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-semibold text-[var(--foreground-secondary)]">
                    <span
                      className={`h-2 w-2 rounded-full ${isReady ? "bg-[var(--success)]" : "animate-pulse bg-[var(--warning)]"}`}
                      aria-hidden
                    />
                    {value}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
