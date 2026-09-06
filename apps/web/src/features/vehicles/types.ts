import type { FuelType, ListingStatus, Transmission } from "@/features/listings/types";

export type MatchCandidateStatus = "PENDING" | "CONFIRMED" | "REJECTED";

export type MarketEstimateMethod = "COMPARABLES_MEDIAN_IQR";

export type VehicleListingSummary = {
  id: string;
  source_id: string;
  external_id: string;
  brand: string;
  model: string;
  year: number;
  mileage_km: number;
  price_amount: string;
  price_currency: string;
  province: string | null;
  status: ListingStatus;
  image_urls: string[];
};

export type MatchCandidate = {
  id: string;
  listing_a_id: string;
  listing_b_id: string;
  confidence_score: string;
  match_reasons: Record<string, unknown>;
  status: MatchCandidateStatus;
  decided_by_user_id: string | null;
  decided_at: string | null;
  created_at: string;
  listing_a: VehicleListingSummary | null;
  listing_b: VehicleListingSummary | null;
};

export type MatchCandidatePage = {
  items: MatchCandidate[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
};

export type ConfirmMatchResponse = {
  candidate_id: string;
  status: MatchCandidateStatus;
  vehicle_id: string;
};

export type RejectMatchResponse = {
  candidate_id: string;
  status: MatchCandidateStatus;
};

export type Vehicle = {
  id: string;
  brand: string;
  model: string;
  generation: string | null;
  trim: string | null;
  engine_code: string | null;
  power_kw: number | null;
  fuel_type: FuelType;
  transmission: Transmission;
  year: number;
  first_listed_at: string;
  listing_count: number;
  created_at: string;
  updated_at: string;
};

export type VehiclePage = {
  items: Vehicle[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
};

export type MarketEstimate = {
  id: string;
  vehicle_id: string | null;
  listing_id: string | null;
  estimated_amount: string;
  low_amount: string;
  high_amount: string;
  currency: string;
  method: MarketEstimateMethod;
  number_of_comparables: number;
  confidence_score: string;
  calculated_at: string;
};

export type VehicleHistoryMetrics = {
  lowest_observed_price: string;
  highest_observed_price: string;
  current_min_price: string;
  days_on_market: number;
  total_price_changes: number;
};

export type VehicleDetail = Vehicle & {
  listings: VehicleListingSummary[];
  history: VehicleHistoryMetrics | null;
  market_estimate: MarketEstimate | null;
};
