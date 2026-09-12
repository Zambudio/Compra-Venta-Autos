import { api } from "@/lib/api";
import type { OwnedVehicleWithDetails, Expense, Sale } from "./types";

export async function getGarageVehicles(): Promise<OwnedVehicleWithDetails[]> {
  const res = await api.get("/garage/vehicles");
  return res.data;
}

export async function purchaseVehicle(payload: {
  opportunity_id: string;
  purchase_price: number;
  vin?: string;
  license_plate?: string;
  notes?: string;
}): Promise<OwnedVehicleWithDetails> {
  const res = await api.post("/garage/purchase", payload);
  return res.data;
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
  const res = await api.post(`/garage/vehicles/${vehicleId}/expenses`, payload);
  return res.data;
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
  const res = await api.post(`/garage/vehicles/${vehicleId}/sale`, payload);
  return res.data;
}
