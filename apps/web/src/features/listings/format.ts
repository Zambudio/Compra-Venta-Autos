import type {
  FuelType,
  ListingStatus,
  SellerType,
  Transmission,
} from "@/features/listings/types";

const numbers = new Intl.NumberFormat("es-ES");
const currency = new Intl.NumberFormat("es-ES", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

export function formatPrice(amount: string, code = "EUR"): string {
  const value = Number(amount);
  if (Number.isNaN(value)) return `${amount} ${code}`;
  return code === "EUR" ? currency.format(value) : `${numbers.format(value)} ${code}`;
}

export function formatKm(km: number): string {
  return `${numbers.format(km)} km`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export const FUEL_LABELS: Record<FuelType, string> = {
  PETROL: "Gasolina",
  DIESEL: "Diésel",
  LPG: "GLP",
  CNG: "GNC",
  HYBRID: "Híbrido",
  PLUGIN_HYBRID: "Híbrido enchufable",
  ELECTRIC: "Eléctrico",
  OTHER: "Otro",
};

export const TRANSMISSION_LABELS: Record<Transmission, string> = {
  MANUAL: "Manual",
  AUTOMATIC: "Automático",
  UNKNOWN: "Sin especificar",
};

export const SELLER_LABELS: Record<SellerType, string> = {
  PRIVATE: "Particular",
  DEALER: "Profesional",
  UNKNOWN: "Sin especificar",
};

export const STATUS_LABELS: Record<ListingStatus, string> = {
  ACTIVE: "Activo",
  WITHDRAWN: "Retirado",
  UNKNOWN: "Desconocido",
};
