export type OpportunityStatus =
  "IDENTIFIED" | "ANALYZING" | "VALIDATED" | "DISCARDED" | "PURCHASED" | "SOLD";

export type SellerPressureLevel = "LOW" | "MEDIUM" | "HIGH";

export type ConfidenceLevel = "LOW" | "MEDIUM" | "HIGH";

export type ScoringComponentKey =
  | "price"
  | "reliability"
  | "liquidity"
  | "mechanical_risk"
  | "mileage"
  | "age"
  | "history"
  | "condition"
  | "listing_age";

export type ScoreBreakdownItem = {
  raw_value?: unknown;
  sub_score?: number;
  score?: number | string;
  weight: number | string;
  weighted_points?: number;
  weighted_score?: number | string;
  reason?: string;
  explanation?: string;
};

export type OpportunityScoreRead = {
  id: string;
  profile_version_id: string;
  total_score?: number | string;
  score_total?: number;
  confidence_score?: number;
  confidence_level?: ConfidenceLevel;
  components?: Record<string, number>;
  price_score?: number | string;
  reliability_score?: number | string;
  liquidity_score?: number | string;
  mechanical_risk_score?: number | string;
  mileage_score?: number | string;
  age_score?: number | string;
  history_score?: number | string;
  condition_score?: number | string;
  listing_age_score?: number | string;
  score_breakdown: Record<string, ScoreBreakdownItem>;
  calculated_at: string;
};

export type OpportunityRead = {
  id: string;
  vehicle_id: string | null;
  listing_id: string | null;
  score_id: string | null;
  status: OpportunityStatus;
  currency: string;

  asking_price: string;
  estimated_market_price: string | null;
  estimated_fast_sale_price: string | null;
  target_purchase_price: string | null;
  estimated_transfer_cost: string;
  estimated_tax: string;
  estimated_repair_min: string;
  estimated_repair_max: string;
  estimated_preparation_cost: string;
  estimated_total_cost_min: string;
  estimated_total_cost_max: string;
  estimated_margin_min: string | null;
  estimated_margin_max: string | null;
  estimated_roi_min: string | null;
  estimated_roi_max: string | null;
  confidence_level: ConfidenceLevel;

  seller_pressure_level: SellerPressureLevel;
  seller_pressure_reasons: string[];
  notes: string | null;

  created_at: string;
  updated_at: string;

  score: OpportunityScoreRead | null;

  // Enriquecidos para renderizado directo
  title: string | null;
  brand: string | null;
  model: string | null;
  generation: string | null;
  trim: string | null;
  engine_code: string | null;
  fuel_type: string | null;
  transmission: string | null;
  year: number | null;
  mileage_km: number | null;
  city: string | null;
  province: string | null;
  external_url: string | null;
  source_name: string | null;
};

export type OpportunityPage = {
  items: OpportunityRead[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
};

export type OpportunityFilterParams = {
  status?: OpportunityStatus | undefined;
  min_score?: number | undefined;
  min_roi?: number | undefined;
  brand?: string | undefined;
  page?: number | undefined;
  pageSize?: number | undefined;
};
