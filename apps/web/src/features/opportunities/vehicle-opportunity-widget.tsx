import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, RefreshCw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { VehicleDetail } from "@/features/vehicles/types";
import type { OpportunityRead } from "@/features/opportunities/types";
import {
  evaluateVehicle,
  getOpportunities,
} from "@/features/opportunities/api";
import { OpportunityCard } from "@/features/opportunities/opportunity-card";

type VehicleOpportunityWidgetProps = {
  vehicle: VehicleDetail;
};

export function VehicleOpportunityWidget({
  vehicle,
}: VehicleOpportunityWidgetProps) {
  const queryClient = useQueryClient();
  const [createdOpportunity, setCreatedOpportunity] =
    useState<OpportunityRead | null>(null);

  // Buscar si ya existe una oportunidad para este vehículo
  const { data: existingData, isLoading: isLoadingExisting } = useQuery({
    queryKey: ["opportunities-by-vehicle", vehicle.id],
    queryFn: async () => {
      const res = await getOpportunities({ pageSize: 50 });
      return res.items.find((o) => o.vehicle_id === vehicle.id) ?? null;
    },
  });

  const opportunity = createdOpportunity || existingData;

  const mutation = useMutation({
    mutationFn: () => evaluateVehicle(vehicle.id),
    onSuccess: (data) => {
      setCreatedOpportunity(data);
      void queryClient.invalidateQueries({
        queryKey: ["opportunities-by-vehicle", vehicle.id],
      });
      void queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
  });

  return (
    <section
      aria-labelledby="vehicle-opportunity-title"
      className="workbench-panel p-5 sm:p-6"
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sparkles className="text-[var(--accent)]" size={20} aria-hidden />
          <h3
            id="vehicle-opportunity-title"
            className="text-base font-bold text-[var(--foreground)]"
          >
            Evaluación de Oportunidad de Compra-Venta
          </h3>
        </div>

        <Button
          type="button"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          variant="secondary"
          size="compact"
          className="text-xs"
        >
          {mutation.isPending ? (
            <>
              <Loader2
                className="mr-1.5 h-3.5 w-3.5 animate-spin"
                aria-hidden
              />
              Evaluando oportunidad…
            </>
          ) : (
            <>
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" aria-hidden />
              {opportunity ? "Reevaluar scoring" : "Evaluar oportunidad ahora"}
            </>
          )}
        </Button>
      </div>

      {mutation.isError && (
        <div
          role="alert"
          className="mb-4 rounded-md border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-600 dark:text-rose-400"
        >
          {mutation.error instanceof Error
            ? mutation.error.message
            : "Error al evaluar la oportunidad del vehículo."}
        </div>
      )}

      {isLoadingExisting && !opportunity ? (
        <p className="text-xs text-[var(--muted)]">
          Comprobando evaluaciones previas…
        </p>
      ) : opportunity ? (
        <div className="mt-2">
          <OpportunityCard opportunity={opportunity} />
        </div>
      ) : (
        <div className="rounded-[var(--radius)] border border-dashed border-[var(--border)] p-6 text-center text-xs text-[var(--muted)]">
          <p>Este vehículo no ha sido evaluado como oportunidad aún.</p>
          <p className="mt-1 text-[0.6875rem] text-[var(--muted-soft)]">
            Haz clic en &ldquo;Evaluar oportunidad ahora&rdquo; para calcular el
            scoring determinista de 9 componentes y los márgenes proyectados con
            marco fiscal español.
          </p>
        </div>
      )}
    </section>
  );
}
