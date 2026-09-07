import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  FileCheck2,
  HelpCircle,
  Plus,
  ShieldAlert,
  Wrench,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { VehicleDetail } from "@/features/vehicles/types";
import {
  addVehicleMitigation,
  getVehicleMitigations,
  lookupVehicleReliability,
} from "./api";
import {
  CLASSIFICATION_LABELS,
  classificationBadgeTone,
  formatEuro,
  SEVERITY_LABELS,
  severityBadgeTone,
} from "./format";
import type { ReliabilityLookupResponse, VehicleMitigation } from "./types";

type VehicleReliabilityWidgetProps = {
  vehicle: VehicleDetail;
};

export function VehicleReliabilityWidget({ vehicle }: VehicleReliabilityWidgetProps) {
  const queryClient = useQueryClient();
  const [showMitigationForm, setShowMitigationForm] = useState(false);
  const [selectedIssueId, setSelectedIssueId] = useState<string>("");
  const [mitigationType, setMitigationType] = useState("INVOICE_PROVED_REPLACEMENT");
  const [description, setDescription] = useState("");

  const {
    data: reliability,
    isLoading: isLoadingReliability,
    isError: isErrorReliability,
  } = useQuery<ReliabilityLookupResponse>({
    queryKey: [
      "reliability-lookup",
      vehicle.brand,
      vehicle.model,
      vehicle.year,
      vehicle.fuel_type,
      vehicle.engine_code,
    ],
    queryFn: () =>
      lookupVehicleReliability({
        brand: vehicle.brand,
        model: vehicle.model,
        year: vehicle.year,
        fuelType: vehicle.fuel_type,
        engineCode: vehicle.engine_code,
      }),
  });

  const { data: mitigations, isLoading: isLoadingMitigations } = useQuery<
    VehicleMitigation[]
  >({
    queryKey: ["vehicle-mitigations", vehicle.id],
    queryFn: () => getVehicleMitigations(vehicle.id),
  });

  const mitigationMutation = useMutation({
    mutationFn: (data: {
      vehicle_id: string;
      known_issue_id: string;
      mitigation_type: string;
      description: string;
    }) => addVehicleMitigation(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["vehicle-mitigations", vehicle.id],
      });
      setShowMitigationForm(false);
      setDescription("");
    },
  });

  if (isLoadingReliability || isLoadingMitigations) {
    return (
      <section
        aria-label="Diagnóstico de fiabilidad técnica"
        className="rounded-[var(--radius)] border border-[var(--border)] bg-white p-5 shadow-xs"
      >
        <p className="text-sm text-[var(--muted)]">
          Consultando base de conocimiento de fiabilidad mecánica…
        </p>
      </section>
    );
  }

  if (isErrorReliability || !reliability) {
    return null;
  }

  const clsTone = classificationBadgeTone(reliability.classification);

  function getStatusIcon(status: string) {
    switch (status) {
      case "WHITELIST":
        return <CheckCircle2 aria-hidden size={18} className="text-[var(--success)]" />;
      case "WATCHLIST":
        return <AlertTriangle aria-hidden size={18} className="text-[var(--warning)]" />;
      case "BLACKLIST":
        return <AlertOctagon aria-hidden size={18} className="text-[var(--danger)]" />;
      default:
        return <HelpCircle aria-hidden size={18} className="text-[var(--muted)]" />;
    }
  }

  return (
    <section
      aria-labelledby="reliability-heading"
      className="flex flex-col gap-5 rounded-[var(--radius)] border border-[var(--border)] bg-white p-5 shadow-xs"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 id="reliability-heading" className="text-base font-bold text-[var(--foreground)]">
              Fiabilidad Mecánica y Diagnóstico
            </h3>
            <span className="text-xs text-[var(--muted)]">(Plan Maestro §15)</span>
          </div>
          <p className="text-xs text-[var(--muted)]">
            Basado en evidencias verificadas para {vehicle.brand} {vehicle.model}
            {vehicle.engine_code ? ` (Motor ${vehicle.engine_code})` : ""}
          </p>
        </div>

        {/* Clasificación explicable */}
        <div className="flex items-center gap-2">
          {getStatusIcon(reliability.classification)}
          <Badge tone={clsTone}>
            {CLASSIFICATION_LABELS[reliability.classification]}
          </Badge>
        </div>
      </div>

      {/* Rationale de la clasificación */}
      {reliability.classification_rationale && (
        <div
          className={`rounded-[var(--radius)] p-3 text-xs border ${
            reliability.classification === "BLACKLIST"
              ? "border-[var(--danger)]/30 bg-[var(--danger)]/5 text-[var(--danger)]"
              : reliability.classification === "WATCHLIST"
                ? "border-[var(--warning)]/30 bg-[var(--warning)]/5 text-[var(--warning)]"
                : "border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)]"
          }`}
        >
          <span className="font-semibold">Justificación técnica objetiva: </span>
          {reliability.classification_rationale}
        </div>
      )}

      {/* Campaña de recall oficial */}
      {reliability.has_recalls && (
        <div className="flex items-start gap-2.5 rounded-[var(--radius)] border border-[var(--danger)] bg-[var(--danger)]/10 p-3 text-xs text-[var(--danger)]">
          <ShieldAlert aria-hidden size={18} className="shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Campaña oficial de revisión o recall detectada:</span>
            <p className="mt-0.5">
              Existen llamadas a revisión emitidas por las autoridades europeas o el fabricante
              relacionadas con este tren motriz. Verifique si esta unidad ha pasado las campañas.
            </p>
          </div>
        </div>
      )}

      {/* Estadísticas de riesgo y costes */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-3 text-center">
          <span className="text-xs text-[var(--muted)]">Problemas documentados</span>
          <p className="mt-1 text-lg font-bold text-[var(--foreground)]">
            {reliability.issues_count}
          </p>
        </div>
        <div className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-3 text-center">
          <span className="text-xs text-[var(--muted)]">Máxima severidad</span>
          <p className="mt-1 text-sm font-bold text-[var(--foreground)]">
            {reliability.max_severity ? SEVERITY_LABELS[reliability.max_severity] : "Ninguna"}
          </p>
        </div>
        <div className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-3 text-center">
          <span className="text-xs text-[var(--muted)]">Riesgo en reparaciones</span>
          <p className="mt-1 text-sm font-bold text-[var(--foreground)]">
            {formatEuro(reliability.total_estimated_repair_min)} – {formatEuro(reliability.total_estimated_repair_max)}
          </p>
        </div>
      </div>

      {/* Lista de problemas conocidos que afectan a este vehículo */}
      {reliability.issues.length > 0 && (
        <div className="flex flex-col gap-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
            Averías conocidas vinculadas a este motor/modelo
          </h4>
          <div className="flex flex-col divide-y divide-[var(--border)] rounded-[var(--radius)] border border-[var(--border)] bg-white">
            {reliability.issues.map((iss) => (
              <div key={iss.id} className="flex flex-col gap-1 p-3 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-[var(--foreground)]">
                      {iss.title}
                    </span>
                    <Badge tone={severityBadgeTone(iss.severity)}>
                      {iss.severity}
                    </Badge>
                  </div>
                  <span className="font-medium text-[var(--muted)]">
                    {formatEuro(iss.estimated_repair_cost_min)} – {formatEuro(iss.estimated_repair_cost_max)}
                  </span>
                </div>
                <p className="text-[var(--muted)]">{iss.description}</p>
                {iss.symptoms && (
                  <p className="text-[var(--foreground)]">
                    <span className="font-medium">Síntomas:</span> {iss.symptoms}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recomendaciones preventivas */}
      {reliability.preventive_recommendations.length > 0 && (
        <div className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-4 text-xs">
          <h4 className="font-bold text-[var(--foreground)] flex items-center gap-1.5 mb-2">
            <Wrench aria-hidden size={14} /> Recomendaciones de Mantenimiento Preventivo
          </h4>
          <ul className="list-disc pl-4 flex flex-col gap-1 text-[var(--muted)]">
            {reliability.preventive_recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Mitigaciones acreditadas en esta unidad (Plan Maestro §15) */}
      <div className="flex flex-col gap-3 rounded-[var(--radius)] border border-[var(--border)] bg-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-bold text-sm text-[var(--foreground)] flex items-center gap-1.5">
              <FileCheck2 aria-hidden size={16} className="text-[var(--success)]" />
              Mitigaciones Acreditadas en esta Unidad
            </h4>
            <p className="text-xs text-[var(--muted)]">
              Reparaciones o piezas sustituidas con factura que reducen el riesgo en esta unidad concreta.
            </p>
          </div>
          {reliability.issues.length > 0 && (
            <button
              type="button"
              onClick={() => {
                setShowMitigationForm(!showMitigationForm);
                if (reliability.issues[0]) {
                  setSelectedIssueId(reliability.issues[0].id);
                }
              }}
              className="inline-flex items-center gap-1 rounded-[var(--radius)] border border-[var(--border)] px-2.5 py-1 text-xs font-medium text-[var(--foreground)] hover:bg-[var(--surface)]"
            >
              <Plus aria-hidden size={13} />
              {showMitigationForm ? "Cancelar" : "Registrar mitigación"}
            </button>
          )}
        </div>

        {/* Formulario de alta de mitigación */}
        {showMitigationForm && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!selectedIssueId || !description.trim()) return;
              mitigationMutation.mutate({
                vehicle_id: vehicle.id,
                known_issue_id: selectedIssueId,
                mitigation_type: mitigationType,
                description: description.trim(),
              });
            }}
            className="flex flex-col gap-3 rounded-[var(--radius)] bg-[var(--surface)] p-3 text-xs border border-[var(--border)]"
          >
            <div>
              <label htmlFor="mitigation-issue-select" className="block font-semibold mb-1">
                Problema mitigado:
              </label>
              <select
                id="mitigation-issue-select"
                value={selectedIssueId}
                onChange={(e) => setSelectedIssueId(e.target.value)}
                className="w-full rounded border border-[var(--border)] bg-white p-1.5 text-xs"
              >
                {reliability.issues.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="mitigation-desc-input" className="block font-semibold mb-1">
                Evidencia / Factura acreditativa:
              </label>
              <Input
                id="mitigation-desc-input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Ej. Correa y bomba de agua sustituidas en concesionario oficial a los 85.000 km con factura nº 2024-118."
                required
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button
                type="submit"
                disabled={mitigationMutation.isPending || !description.trim()}
              >
                {mitigationMutation.isPending ? "Guardando…" : "Guardar Mitigación"}
              </Button>
            </div>
          </form>
        )}

        {/* Lista de mitigaciones existentes */}
        {mitigations && mitigations.length > 0 ? (
          <ul className="flex flex-col gap-2">
            {mitigations.map((m) => (
              <li
                key={m.id}
                className="flex flex-col gap-0.5 rounded border border-[var(--border)] bg-[var(--surface)] p-2.5 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[var(--success)]">
                    {m.known_issue?.title ?? "Avería mitigada"}
                  </span>
                  <Badge tone="success">Acreditado con factura</Badge>
                </div>
                <p className="text-[var(--foreground)]">{m.description}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-[var(--muted)] italic">
            No se han registrado mitigaciones documentadas para esta unidad.
          </p>
        )}
      </div>
    </section>
  );
}
