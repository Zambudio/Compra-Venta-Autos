import type { OpportunityRead } from "@/features/opportunities/types";

export type InspectionStatus = "DRAFT" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";
export type CheckResult = "PASS" | "WARNING" | "FAIL" | "NOT_CHECKED";

export type WatchlistEntryPublic = {
  id: string;
  opportunity_id: string;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type WatchlistEntryWithOpportunity = WatchlistEntryPublic & {
  opportunity: OpportunityRead;
};

export type InspectionCheckPublic = {
  id: string;
  inspection_id: string;
  category: string;
  name: string;
  description: string | null;
  known_issue_id: string | null;
  result: CheckResult;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type InspectionPublic = {
  id: string;
  watchlist_entry_id: string;
  status: InspectionStatus;
  inspector_name: string | null;
  scheduled_at: string | null;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type InspectionWithDetails = InspectionPublic & {
  checks: InspectionCheckPublic[];
};

export type FileAttachmentPublic = {
  id: string;
  inspection_id: string;
  file_name: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
  updated_at: string;
};
