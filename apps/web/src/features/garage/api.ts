import { apiRequest } from "@/lib/api";
import type { OwnedVehicleWithDetails, Expense, Sale } from "./types";

export async function getGarageVehicles(): Promise<OwnedVehicleWithDetails[]> {
  const res = await apiRequest<OwnedVehicleWithDetails[]>('/garage/vehicles');
  return res;
}

export async function purchaseVehicle(payload: {
  opportunity_id: string;
  purchase_price: number;
  vin?: string;
  license_plate?: string;
  notes?: string;
}): Promise<OwnedVehicleWithDetails> {
  const res = await apiRequest<OwnedVehicleWithDetails>('/garage/purchase', { method: 'POST', body: JSON.stringify(payload) });
  return res;
}

export async function addExpense(
  vehicleId: string,
  payload: {
    amount: number;
    category: string;
    description: string;
    expense_date: string;
  }
): Promise<Expense> {
  const res = await apiRequest<Expense>(`/garage/vehicles/${vehicleId}/expenses`, { method: 'POST', body: JSON.stringify(payload) });
  return res;
}

export async function registerSale(
  vehicleId: string,
  payload: {
    sale_price: number;
    sale_date: string;
    buyer_info?: string;
    notes?: string;
  }
): Promise<Sale> {
  const res = await apiRequest<Sale>(`/garage/vehicles/${vehicleId}/sale`, { method: 'POST', body: JSON.stringify(payload) });
  return res;
}
