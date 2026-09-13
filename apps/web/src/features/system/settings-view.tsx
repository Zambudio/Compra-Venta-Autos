"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Settings, Play, Square, Activity } from "lucide-react";
import { StatusView } from "./status-view";
import { getSources, updateSource, checkSourceHealth, type Source } from "./api";
import { Button } from "@/components/ui/button";

export function SettingsView() {
  const queryClient = useQueryClient();
  const { data: sources, isLoading } = useQuery({
    queryKey: ["sources"],
    queryFn: getSources,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ key, is_active }: { key: string; is_active: boolean }) => updateSource(key, is_active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
  });

  const checkHealthMutation = useMutation({
    mutationFn: (key: string) => checkSourceHealth(key),
    onSuccess: (data) => {
      alert(`Estado de ${data.source_key}:\nSano: ${data.healthy}\nDetalle: ${data.detail}`);
    },
    onError: (err) => {
      alert(`Error al comprobar estado: ${err instanceof Error ? err.message : 'desconocido'}`);
    }
  });

  return (
    <div className="space-y-8 animate-in fade-in-50">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 mb-6 flex items-center">
          <Settings className="h-6 w-6 mr-2 text-indigo-600" />
          Configuración del Sistema
        </h2>
        <div className="grid gap-6 md:grid-cols-2">
          {/* Status Section */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-medium mb-4 flex items-center">
              <Activity className="h-5 w-5 mr-2 text-blue-500" />
              Estado de la Plataforma
            </h3>
            <StatusView />
          </div>

          {/* Connectors Section */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-medium mb-4 flex items-center">
              <Activity className="h-5 w-5 mr-2 text-green-500" />
              Gestión de Conectores
            </h3>
            {isLoading ? (
              <p className="text-sm text-slate-500">Cargando fuentes...</p>
            ) : (
              <div className="space-y-4">
                {sources?.map((source) => (
                  <div key={source.key} className="flex items-center justify-between p-4 border border-slate-100 rounded-lg bg-slate-50">
                    <div>
                      <p className="font-medium text-slate-900">{source.name}</p>
                      <p className="text-xs text-slate-500 capitalize">Tipo: {source.provider_kind.toLowerCase()}</p>
                      <p className="text-xs mt-1">
                        Estado: <span className={source.is_active ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>
                          {source.is_active ? "Activo" : "Inactivo"}
                        </span>
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => checkHealthMutation.mutate(source.key)}
                        disabled={checkHealthMutation.isPending}
                      >
                        Probar
                      </Button>
                      <Button
                        size="sm"
                        variant={source.is_active ? "destructive" : "default"}
                        onClick={() => toggleMutation.mutate({ key: source.key, is_active: !source.is_active })}
                        disabled={toggleMutation.isPending}
                      >
                        {source.is_active ? <Square className="h-4 w-4 mr-1" /> : <Play className="h-4 w-4 mr-1" />}
                        {source.is_active ? "Desactivar" : "Activar"}
                      </Button>
                    </div>
                  </div>
                ))}
                {sources?.length === 0 && (
                  <p className="text-sm text-slate-500">No hay conectores registrados.</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
