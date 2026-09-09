import { ArrowRight, CarFront, Fuel, Gauge, Layers3 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { FUEL_LABELS, TRANSMISSION_LABELS } from "@/features/vehicles/format";
import type { Vehicle } from "@/features/vehicles/types";

type VehicleCardProps = {
  vehicle: Vehicle;
  onSelect: (vehicle: Vehicle) => void;
};

export function VehicleCard({ vehicle, onSelect }: VehicleCardProps) {
  const fuel = FUEL_LABELS[vehicle.fuel_type] ?? vehicle.fuel_type;
  const transmission =
    TRANSMISSION_LABELS[vehicle.transmission] ?? vehicle.transmission;

  return (
    <article className="group flex min-h-full flex-col rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface-raised)] p-5 shadow-[var(--shadow-card)] transition-[border-color,box-shadow,transform] duration-200 ease-[cubic-bezier(0.23,1,0.32,1)] hover:-translate-y-0.5 hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-raised)]">
      <div className="flex items-start justify-between gap-3">
        <span className="grid h-10 w-10 place-items-center rounded-[var(--radius-control)] bg-[var(--accent-soft)] text-[var(--accent)]">
          <CarFront aria-hidden size={20} strokeWidth={1.8} />
        </span>
        <Badge tone="neutral">
          <Layers3 aria-hidden size={12} className="mr-1" />
          {vehicle.listing_count}{" "}
          {vehicle.listing_count === 1 ? "anuncio" : "anuncios"}
        </Badge>
      </div>

      <div className="mt-5">
        <p className="eyebrow">Unidad consolidada</p>
        <h3 className="font-display mt-1 text-xl leading-tight font-semibold tracking-[-0.025em]">
          {vehicle.brand} {vehicle.model}
        </h3>
        <p className="mt-1 min-h-5 text-sm text-[var(--muted)]">
          {vehicle.trim ?? "Versión sin especificar"}
        </p>
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-px overflow-hidden rounded-[var(--radius-control)] bg-[var(--border)]">
        <div className="bg-[var(--surface-inset)] p-3">
          <dt className="eyebrow flex items-center gap-1">
            <Gauge aria-hidden size={12} />
            Año
          </dt>
          <dd className="font-data mt-1 font-semibold">{vehicle.year}</dd>
        </div>
        <div className="bg-[var(--surface-inset)] p-3">
          <dt className="eyebrow flex items-center gap-1">
            <Fuel aria-hidden size={12} />
            Combustible
          </dt>
          <dd className="mt-1 truncate font-semibold">{fuel}</dd>
        </div>
        <div className="bg-[var(--surface-inset)] p-3">
          <dt className="eyebrow">Cambio</dt>
          <dd className="mt-1 truncate font-semibold">{transmission}</dd>
        </div>
        <div className="bg-[var(--surface-inset)] p-3">
          <dt className="eyebrow">Potencia</dt>
          <dd className="font-data mt-1 font-semibold">
            {vehicle.power_kw ? `${vehicle.power_kw} kW` : "—"}
          </dd>
        </div>
      </dl>

      <button
        type="button"
        onClick={() => onSelect(vehicle)}
        className="mt-5 inline-flex min-h-11 w-full items-center justify-between rounded-[var(--radius-control)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-3.5 text-sm font-semibold text-[var(--foreground)] transition-[background-color,border-color,transform] duration-150 hover:border-[var(--accent)] hover:bg-[var(--accent-soft)] active:scale-[0.98]"
        aria-label={`Ver detalles de ${vehicle.brand} ${vehicle.model}`}
      >
        Abrir ficha consolidada
        <ArrowRight
          aria-hidden
          size={16}
          className="transition-transform duration-150 group-hover:translate-x-0.5"
        />
      </button>
    </article>
  );
}
