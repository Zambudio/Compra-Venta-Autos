"use client";

import { useQuery } from "@tanstack/react-query";
import { getGarageVehicles } from "./api";
import { Car, Wrench, DollarSign, ArrowRightLeft } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function GarageView() {
  const { data: vehicles, isLoading } = useQuery({
    queryKey: ["garage"],
    queryFn: getGarageVehicles,
  });

  if (isLoading) {
    return <div className="p-8 text-center text-[var(--muted)]">Cargando Garage...</div>;
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <header className="border-b border-[var(--border)] bg-[var(--background)] px-6 py-6">
        <h1 className="text-2xl font-bold tracking-tight">Garage & Inventario</h1>
        <p className="text-[var(--muted)]">
          GestiÃ³n de vehÃ­culos adquiridos, gastos de reacondicionamiento y rentabilidad.
        </p>
      </header>

      <main className="flex-1 p-6">
        {vehicles?.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-[var(--radius-card)] border border-dashed p-12 text-center text-[var(--muted)]">
            <Car size={48} className="mb-4 opacity-50" />
            <h2 className="text-lg font-semibold text-[var(--foreground)]">Garage vacÃ­o</h2>
            <p>No hay vehÃ­culos en inventario. Compra una oportunidad desde la Watchlist.</p>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {vehicles?.map((vehicle) => (
              <div
                key={vehicle.id}
                className="flex flex-col rounded-[var(--radius-card)] border bg-[var(--surface)] shadow-sm"
              >
                <div className="border-b p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold">{vehicle.license_plate || "Sin MatrÃ­cula"}</h3>
                      <p className="text-xs text-[var(--muted)]">VIN: {vehicle.vin || "N/A"}</p>
                    </div>
                    <Badge tone={vehicle.sale ? "success" : "warning"}>
                      {vehicle.sale ? "Vendido" : "En Stock"}
                    </Badge>
                  </div>
                </div>

                <div className="flex-1 p-4 text-sm">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center text-[var(--muted)]">
                        <ArrowRightLeft size={14} className="mr-2" />
                        Compra
                      </span>
                      <span className="font-medium">{Number(vehicle.purchase_price).toLocaleString()} â‚¬</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center text-[var(--muted)]">
                        <Wrench size={14} className="mr-2" />
                        Gastos ({vehicle.expenses.length})
                      </span>
                      <span className="font-medium text-[var(--danger)]">
                        + {Number(vehicle.total_expenses).toLocaleString()} â‚¬
                      </span>
                    </div>

                    <div className="flex items-center justify-between border-t pt-2">
                      <span className="font-semibold text-[var(--foreground)]">Coste Total</span>
                      <span className="font-semibold">{Number(vehicle.total_cost).toLocaleString()} â‚¬</span>
                    </div>
                  </div>

                  {vehicle.sale && (
                    <div className="mt-4 space-y-3 rounded-md bg-[var(--success-soft)] p-3">
                      <div className="flex items-center justify-between">
                        <span className="flex items-center text-[var(--success)]">
                          <DollarSign size={14} className="mr-2" />
                          Venta
                        </span>
                        <span className="font-medium text-[var(--success)]">
                          {Number(vehicle.sale.sale_price).toLocaleString()} â‚¬
                        </span>
                      </div>
                      <div className="flex items-center justify-between border-t border-[color-mix(in_srgb,var(--success)_22%,transparent)] pt-2 font-bold text-[var(--success)]">
                        <span>Beneficio Neto</span>
                        <div className="text-right">
                          <p>{Number(vehicle.net_profit).toLocaleString()} â‚¬</p>
                          <p className="text-xs opacity-80">ROI: {Number(vehicle.roi_percentage).toFixed(1)}%</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
