import { Car, Layers } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { FUEL_LABELS, TRANSMISSION_LABELS } from "@/features/vehicles/format";
import type { Vehicle } from "@/features/vehicles/types";

type VehicleCardProps = {
  vehicle: Vehicle;
  onSelect: (vehicle: Vehicle) => void;
};

export function VehicleCard({ vehicle, onSelect }: VehicleCardProps) {
  const fuel = FUEL_LABELS[vehicle.fuel_type] ?? vehicle.fuel_type;
  const transmission = TRANSMISSION_LABELS[vehicle.transmission] ?? vehicle.transmission;

  return (
    <article className="flex flex-col justify-between rounded-[var(--radius)] border border-[var(--border)] bg-white p-5 shadow-xs transition-shadow hover:shadow-sm">
      <div className="flex flex-col gap-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold tracking-tight text-[var(--foreground)]">
              {vehicle.brand} {vehicle.model}
            </h3>
            {vehicle.trim && (
              <p className="text-xs text-[var(--muted)]">{vehicle.trim}</p>
            )}
          </div>
          <Badge tone="neutral">
            <span className="inline-flex items-center gap-1">
              <Layers aria-hidden size={12} />
              {vehicle.listing_count} {vehicle.listing_count === 1 ? "anuncio" : "anuncios"}
            </span>
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs text-[var(--muted)]">
          <div>
            <span className="font-medium text-[var(--foreground)]">Año:</span> {vehicle.year}
          </div>
          <div>
            <span className="font-medium text-[var(--foreground)]">Combustible:</span> {fuel}
          </div>
          <div>
            <span className="font-medium text-[var(--foreground)]">Cambio:</span> {transmission}
          </div>
          {vehicle.power_kw && (
            <div>
              <span className="font-medium text-[var(--foreground)]">Potencia:</span> {vehicle.power_kw} kW
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-[var(--border)]">
        <button
          type="button"
          onClick={() => onSelect(vehicle)}
          className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-[var(--radius)] border border-[var(--border)] bg-white px-3 text-sm font-medium text-[var(--foreground)] transition-colors hover:bg-[var(--surface-hover)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]"
          aria-label={`Ver detalles de ${vehicle.brand} ${vehicle.model}`}
        >
          <Car aria-hidden size={16} />
          Ver ficha del vehículo
        </button>
      </div>
    </article>
  );
}
