"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  CheckCircle2,
  CircleAlert,
  RefreshCw,
  Settings,
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { User } from "@/features/auth/types";
import {
  checkSourceHealth,
  getSources,
  syncSource,
  updateSource,
  type Source,
  type SourceHealth,
} from "@/features/system/api";
import { StatusView } from "@/features/system/status-view";
import { ApiError } from "@/lib/api";

type SettingsViewProps = {
  userRole: User["role"];
};

type Notice = { kind: "success" | "error"; text: string };

export function SettingsView({ userRole }: SettingsViewProps) {
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<Notice>();
  const [healthBySource, setHealthBySource] = useState<
    Record<string, SourceHealth>
  >({});
  const canManage = userRole === "OWNER" || userRole === "ADMIN";
  const sourcesQuery = useQuery({
    queryKey: ["sources"],
    queryFn: getSources,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ key, enabled }: { key: string; enabled: boolean }) =>
      updateSource(key, enabled),
    onSuccess: (configuration, variables) => {
      queryClient.setQueryData<Source[]>(["sources"], (current) =>
        current?.map((source) =>
          source.key === variables.key
            ? {
                ...source,
                enabled: configuration.enabled,
                is_active: configuration.enabled,
                config: configuration.config,
                last_sync: configuration.last_sync,
                sync_error: configuration.sync_error,
                health: configuration.enabled ? "ok" : "disabled",
              }
            : source,
        ),
      );
      setNotice({
        kind: "success",
        text: `Conector ${variables.key} ${variables.enabled ? "activado" : "desactivado"}.`,
      });
    },
    onError: (error) => {
      const isLastSource =
        error instanceof ApiError && error.code === "active_source_required";
      setNotice({
        kind: "error",
        text: isLastSource
          ? "Mantén al menos un conector activo."
          : "No se pudo actualizar el conector.",
      });
    },
  });

  const healthMutation = useMutation({
    mutationFn: (key: string) => checkSourceHealth(key),
    onSuccess: (health) => {
      setHealthBySource((current) => ({
        ...current,
        [health.source_key]: health,
      }));
    },
    onError: () =>
      setNotice({ kind: "error", text: "No se pudo comprobar el conector." }),
  });

  const syncMutation = useMutation({
    mutationFn: (key: string) => syncSource(key),
    onSuccess: (run) => {
      setNotice({
        kind: "success",
        text: `Sincronización de ${sourceName(sourcesQuery.data, run.source_key)} completada.`,
      });
      void queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: () =>
      setNotice({
        kind: "error",
        text: "No se pudo forzar la sincronización.",
      }),
  });

  return (
    <section className="page-frame max-w-6xl">
      <p className="eyebrow">Operaciones / Sistema</p>
      <h1 className="page-title mt-1 flex items-center gap-2">
        <Settings aria-hidden size={24} />
        Configuración
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
        Supervisa la plataforma y controla las fuentes que alimentan el radar.
      </p>

      {notice ? (
        <div
          className={`mt-5 flex items-center gap-2 rounded-[var(--radius-control)] px-4 py-3 text-sm ${notice.kind === "error" ? "bg-[var(--danger-soft)] text-[var(--danger)]" : "bg-[var(--success-soft)] text-[var(--success)]"}`}
          role={notice.kind === "error" ? "alert" : "status"}
        >
          {notice.kind === "error" ? (
            <CircleAlert aria-hidden size={18} />
          ) : (
            <CheckCircle2 aria-hidden size={18} />
          )}
          {notice.text}
        </div>
      ) : null}

      <div className="mt-8 grid items-start gap-7 xl:grid-cols-[1.05fr_0.95fr]">
        <section aria-labelledby="platform-status-title">
          <h2 id="platform-status-title" className="section-title mb-3">
            Estado de la plataforma
          </h2>
          <StatusView />
        </section>

        <section aria-labelledby="connectors-title">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 id="connectors-title" className="section-title">
              Gestión de conectores
            </h2>
            {!canManage ? (
              <span className="rounded-full bg-[var(--surface-inset)] px-2.5 py-1 text-xs font-semibold text-[var(--muted)]">
                Solo lectura
              </span>
            ) : null}
          </div>

          {sourcesQuery.isPending ? (
            <div
              className="workbench-panel p-5 text-sm text-[var(--muted)]"
              aria-busy="true"
            >
              Cargando conectores…
            </div>
          ) : sourcesQuery.isError ? (
            <div
              className="workbench-panel p-5 text-sm text-[var(--danger)]"
              role="alert"
            >
              No se pudieron cargar los conectores.
            </div>
          ) : (
            <div className="workbench-panel divide-y divide-[var(--border)] overflow-hidden">
              {sourcesQuery.data.map((source) => {
                const isSaving =
                  toggleMutation.isPending &&
                  toggleMutation.variables?.key === source.key;
                const isChecking =
                  healthMutation.isPending &&
                  healthMutation.variables === source.key;
                const isSyncing =
                  syncMutation.isPending &&
                  syncMutation.variables === source.key;
                const observedHealth = healthBySource[source.key];
                const healthy = observedHealth
                  ? observedHealth.healthy
                  : source.health === "ok";

                return (
                  <article key={source.key} className="p-5">
                    <div className="flex items-start justify-between gap-5">
                      <div>
                        <h3 className="font-semibold">{source.name}</h3>
                        <p className="mt-1 text-xs text-[var(--muted)]">
                          {source.provider_kind === "MANUAL"
                            ? "Entrada controlada por el equipo"
                            : "Consulta de mercado en tiempo real"}
                        </p>
                      </div>
                      <button
                        type="button"
                        role="switch"
                        aria-label={source.name}
                        aria-checked={source.enabled}
                        disabled={!canManage || isSaving}
                        onClick={() =>
                          toggleMutation.mutate({
                            key: source.key,
                            enabled: !source.enabled,
                          })
                        }
                        className={`relative h-7 w-12 rounded-full transition-colors focus-visible:ring-4 focus-visible:ring-[var(--focus-ring)] focus-visible:outline-none disabled:opacity-45 ${source.enabled ? "bg-[var(--success)]" : "bg-[var(--border-strong)]"}`}
                      >
                        <span
                          aria-hidden
                          className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${source.enabled ? "translate-x-6" : "translate-x-1"}`}
                        />
                      </button>
                    </div>

                    <div className="mt-4 grid gap-2 text-xs text-[var(--muted)] sm:grid-cols-2">
                      <p>
                        Estado: {source.enabled ? "Activo" : "Inactivo"}
                        {isSaving ? " · Guardando…" : ""}
                      </p>
                      <p>
                        Salud:{" "}
                        {observedHealth?.detail ??
                          (healthy ? "Saludable" : "No disponible")}
                      </p>
                      <p className="sm:col-span-2">
                        Última sincronización:{" "}
                        {formatLastSync(source.last_sync)}
                      </p>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <Button
                        size="compact"
                        variant="secondary"
                        aria-label={`Comprobar ${source.name}`}
                        disabled={isChecking}
                        onClick={() => healthMutation.mutate(source.key)}
                      >
                        <Activity aria-hidden size={15} />
                        {isChecking ? "Comprobando…" : "Comprobar"}
                      </Button>
                      {source.is_automatable ? (
                        <Button
                          size="compact"
                          variant="secondary"
                          aria-label={`Forzar sincronización de ${source.name}`}
                          disabled={!canManage || !source.enabled || isSyncing}
                          onClick={() => syncMutation.mutate(source.key)}
                        >
                          <RefreshCw
                            aria-hidden
                            size={15}
                            className={isSyncing ? "animate-spin" : undefined}
                          />
                          {isSyncing
                            ? "Sincronizando…"
                            : "Forzar sincronización"}
                        </Button>
                      ) : null}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

function sourceName(sources: Source[] | undefined, key: string): string {
  return sources?.find((source) => source.key === key)?.name ?? key;
}

function formatLastSync(value: string | null): string {
  if (!value) return "Nunca";
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}
