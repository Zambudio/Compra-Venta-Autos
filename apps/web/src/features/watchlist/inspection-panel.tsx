"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, FileText } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { WatchlistEntryWithOpportunity } from "./types";
import { getInspections, createInspection } from "./api";
import { InspectionDetail } from "./inspection-detail";

export function InspectionPanel({
  entry,
  onBack,
}: {
  entry: WatchlistEntryWithOpportunity;
  onBack: () => void;
}) {
  const queryClient = useQueryClient();
  const [activeInspectionId, setActiveInspectionId] = useState<string | null>(null);

  const { data: inspections, isLoading } = useQuery({
    queryKey: ["inspections", entry.id],
    queryFn: () => getInspections(entry.id),
  });

  const createMutation = useMutation({
    mutationFn: () => createInspection(entry.id, "Inspector AutomÃ¡tico", new Date().toISOString()),
    onSuccess: (newInspection) => {
      queryClient.invalidateQueries({ queryKey: ["inspections", entry.id] });
      setActiveInspectionId(newInspection.id);
    },
  });

  const activeInspection = inspections?.find((i) => i.id === activeInspectionId);

  if (activeInspection) {
    return (
      <InspectionDetail
        inspection={activeInspection}
        onBack={() => setActiveInspectionId(null)}
      />
    );
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-[var(--border)] p-4">
        <Button variant="ghost" size="icon" onClick={onBack} className="lg:hidden" aria-label="Volver">
          <ArrowLeft size={20} />
        </Button>
        <div className="min-w-0 flex-1">
          <h2 className="truncate font-semibold text-[var(--foreground)]">
            {entry.opportunity.title}
          </h2>
          <p className="text-xs text-[var(--muted)]">Listado de inspecciones</p>
        </div>
        <Button
          size="compact"
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
        >
          <Plus size={16} className="mr-1" />
          Nueva InspecciÃ³n
        </Button>
      </header>

      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <p className="text-sm text-[var(--muted)]">Cargando inspecciones...</p>
        ) : inspections?.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText size={48} className="mb-4 text-[var(--border-strong)]" strokeWidth={1} />
            <p className="text-[var(--foreground)] font-medium">No hay inspecciones</p>
            <p className="text-sm text-[var(--muted)]">
              Inicia una inspecciÃ³n para empezar a rellenar el checklist.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            {inspections?.map((inspection) => (
              <button
                key={inspection.id}
                onClick={() => setActiveInspectionId(inspection.id)}
                className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--background)] p-4 text-left transition-colors hover:border-[var(--border-strong)]"
              >
                <div className="flex items-center justify-between w-full">
                  <Badge
                    tone="neutral"
                    className={
                      inspection.status === "COMPLETED"
                        ? "border-[#4ade80] text-[#4ade80]"
                        : inspection.status === "IN_PROGRESS"
                        ? "border-[#fbbf24] text-[#fbbf24]"
                        : "text-[var(--muted)]"
                    }
                  >
                    {inspection.status}
                  </Badge>
                  <span className="text-xs text-[var(--muted)]">
                    {new Date(inspection.created_at).toLocaleDateString()}
                  </span>
                </div>
                
                <div>
                  <p className="font-medium text-[var(--foreground)]">
                    {inspection.inspector_name || "Sin inspector asignado"}
                  </p>
                  <p className="text-xs text-[var(--muted)] mt-1">
                    {inspection.checks.length} puntos revisados
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
