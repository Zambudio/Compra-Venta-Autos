export type ExpenseCategory = "REPAIR" | "TRANSPORT" | "TAX" | "FEE" | "OTHER";

export type Expense = {
  id: string;
  vehicle_id: string;
  amount: number | string;
  category: ExpenseCategory;
  description: string;
  expense_date: string;
  receipt_file_id: string | null;
  created_at: string;
  updated_at: string;
};

export type Sale = {
  id: string;
  vehicle_id: string;
  sale_price: number | string;
  sale_date: string;
  buyer_info: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type OwnedVehicleWithDetails = {
  id: string;
  opportunity_id: string;
  purchase_price: number | string;
  purchase_date: string;
  vin: string | null;
  license_plate: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  expenses: Expense[];
  sale: Sale | null;
  total_expenses: number | string;
  total_cost: number | string;
  net_profit: number | string | null;
  roi_percentage: number | string | null;
};
