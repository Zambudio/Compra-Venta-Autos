export type SourceTrustLevel = "A" | "B" | "C" | "D";

export type KnowledgeSourceType =
  | "OFFICIAL_RECALL"
  | "STATISTICAL_REPORT"
  | "TECHNICAL_MEDIA"
  | "COMMUNITY_EXPERIENCE";

export type IssueSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type IssueFrequency = "RARE" | "OCCASIONAL" | "FREQUENT" | "SYSTEMIC";

export type IssueStatus = "DRAFT" | "REVIEWED" | "VERIFIED" | "DEPRECATED";

export type VehicleComponent =
  | "ENGINE_INTERNAL"
  | "TIMING_SYSTEM"
  | "FUEL_INJECTION"
  | "TURBOCHARGER"
  | "COOLING_SYSTEM"
  | "EXHAUST_EMISSIONS"
  | "TRANSMISSION_MANUAL"
  | "TRANSMISSION_AUTOMATIC"
  | "ELECTRICAL_HYBRID"
  | "BRAKING"
  | "SUSPENSION_STEERING"
  | "CHASSIS_BODY";

export type ClassificationStatus =
  | "WHITELIST"
  | "WATCHLIST"
  | "BLACKLIST"
  | "UNKNOWN";

export type ClassificationTargetType =
  | "MANUFACTURER"
  | "MODEL"
  | "GENERATION"
  | "ENGINE"
  | "ENGINE_VARIANT"
  | "TRANSMISSION";

export type TransmissionType =
  | "MANUAL"
  | "TORQUE_CONVERTER"
  | "DUAL_CLUTCH"
  | "CVT"
  | "AUTOMATED_MANUAL"
  | "DIRECT_DRIVE_EV";

export type EngineAspiration =
  | "NATURALLY_ASPIRATED"
  | "TURBOCHARGED"
  | "TWIN_TURBO"
  | "SUPERCHARGED";

export type Manufacturer = {
  id: string;
  name: string;
  country: string | null;
  created_at: string;
  updated_at: string;
};

export type VehicleModel = {
  id: string;
  manufacturer_id: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export type VehicleGeneration = {
  id: string;
  model_id: string;
  name: string;
  year_start: number;
  year_end: number | null;
  created_at: string;
  updated_at: string;
};

export type Engine = {
  id: string;
  manufacturer_id: string;
  family_code: string;
  name: string;
  displacement_cc: number | null;
  fuel_type: string;
  aspiration: EngineAspiration;
  created_at: string;
  updated_at: string;
};

export type EngineVariant = {
  id: string;
  engine_id: string;
  version_code: string | null;
  power_kw: number | null;
  power_cv: number | null;
  torque_nm: number | null;
  year_start: number | null;
  year_end: number | null;
  created_at: string;
  updated_at: string;
};

export type TransmissionSpec = {
  id: string;
  manufacturer_id: string | null;
  code: string | null;
  name: string;
  type: TransmissionType;
  gears: number | null;
  created_at: string;
  updated_at: string;
};

export type KnowledgeSource = {
  id: string;
  source_type: KnowledgeSourceType;
  name: string;
  url: string | null;
  publisher: string | null;
  published_at: string | null;
  retrieved_at: string;
  trust_level: SourceTrustLevel;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type Evidence = {
  id: string;
  source_id: string;
  component: VehicleComponent;
  summary: string;
  severity: IssueSeverity;
  confidence_score: string;
  verified: boolean;
  verified_by_user_id: string | null;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
  source?: KnowledgeSource | null;
};

export type KnownIssue = {
  id: string;
  title: string;
  description: string;
  component: VehicleComponent;
  severity: IssueSeverity;
  frequency: IssueFrequency;
  typical_mileage_km: number | null;
  estimated_repair_cost_min: string;
  estimated_repair_cost_max: string;
  currency: string;
  symptoms: string | null;
  prevention: string | null;
  definitive_repair: string | null;
  has_recall_campaign: boolean;
  recall_details: string | null;
  status: IssueStatus;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  evidences?: Evidence[];
  engines?: Engine[];
  generations?: VehicleGeneration[];
};

export type KnownIssuePage = {
  items: KnownIssue[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
};

export type VehicleClassification = {
  id: string;
  target_type: ClassificationTargetType;
  target_id: string;
  status: ClassificationStatus;
  rationale: string;
  validity_start: string | null;
  validity_end: string | null;
  created_at: string;
  updated_at: string;
};

export type VehicleClassificationPage = {
  items: VehicleClassification[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
};

export type VehicleMitigation = {
  id: string;
  vehicle_id: string;
  known_issue_id: string;
  mitigation_type: string;
  description: string;
  applied_at: string;
  verified_by_user_id: string | null;
  created_at: string;
  updated_at: string;
  known_issue?: KnownIssue | null;
};

export type ReliabilityLookupResponse = {
  brand: string;
  model: string;
  year: number | null;
  fuel_type: string | null;
  engine_code: string | null;
  classification: ClassificationStatus;
  classification_rationale: string | null;
  issues_count: number;
  max_severity: IssueSeverity | null;
  total_estimated_repair_min: string;
  total_estimated_repair_max: string;
  currency: string;
  has_recalls: boolean;
  issues: KnownIssue[];
  preventive_recommendations: string[];
};
