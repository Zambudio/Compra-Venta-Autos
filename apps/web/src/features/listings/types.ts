export type FuelType =
  | "PETROL"
  | "DIESEL"
  | "LPG"
  | "CNG"
  | "HYBRID"
  | "PLUGIN_HYBRID"
  | "ELECTRIC"
  | "OTHER";

export type Transmission = "MANUAL" | "AUTOMATIC" | "UNKNOWN";
export type SellerType = "PRIVATE" | "DEALER" | "UNKNOWN";
export type ListingStatus = "ACTIVE" | "WITHDRAWN" | "UNKNOWN";
export type SortOrder = "newest" | "price_asc" | "price_desc";

export type Listing = {
  id: string;
  source_key: string;
  external_id: string;
  url: string | null;
  brand: string;
  model: string;
  generation: string | null;
  trim: string | null;
  engine_code: string | null;
  power_kw: number | null;
  fuel_type: FuelType;
  transmission: Transmission;
  year: number;
  mileage_km: number;
  price_amount: string;
  price_currency: string;
  location: string | null;
  province: string | null;
  seller_type: SellerType;
  description: string | null;
  image_urls: string[];
  status: ListingStatus;
  first_seen_at: string;
  last_seen_at: string;
  published_at: string | null;
};

export type SnapshotEntry = {
  observed_at: string;
  price_amount: string;
  price_currency: string;
  mileage_km: number;
  status: ListingStatus;
};

export type ListingDetail = Listing & { snapshots: SnapshotEntry[] };

export type ListingPage = {
  items: Listing[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
};

export type ListingFilters = {
  brand?: string;
  model?: string;
  year_min?: number;
  year_max?: number;
  price_min?: number;
  price_max?: number;
  fuel_type?: FuelType;
  mileage_max?: number;
  province?: string;
  seller_type?: SellerType;
  source?: string[];
  status?: ListingStatus;
  sort?: SortOrder;
  page?: number;
  page_size?: number;
};

export type ComplianceReview = {
  acquisition_method: string;
  automated_allowed: boolean;
  authentication_required: string;
  rate_limit: string | null;
  terms_url: string | null;
  checked_at: string;
  notes: string;
};

export type Source = {
  key: string;
  name: string;
  provider_kind: "MOCK" | "MANUAL" | "CONNECTOR";
  is_active: boolean;
  is_automatable: boolean;
  latest_review: ComplianceReview | null;
};

export type SyncRunStatus =
  | "PENDING"
  | "RUNNING"
  | "SUCCESS"
  | "PARTIAL"
  | "FAILED";

export type SyncRun = {
  id: string;
  source_key: string;
  status: SyncRunStatus;
  mode: string;
  listings_seen: number;
  listings_created: number;
  listings_updated: number;
  snapshots_created: number;
  error_summary: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type ManualListingInput = {
  url?: string;
  brand: string;
  model: string;
  trim?: string;
  year: number;
  mileage_km: number;
  price_amount: string;
  fuel_type: FuelType;
  transmission: Transmission;
  seller_type: SellerType;
  province?: string;
  description?: string;
};
