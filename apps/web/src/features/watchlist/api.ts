import { apiRequest, readCookie } from "@/lib/api";
import type {
  WatchlistEntryWithOpportunity,
  WatchlistEntryPublic,
  InspectionWithDetails,
  InspectionPublic,
  InspectionCheckPublic,
  FileAttachmentPublic,
  InspectionStatus,
  CheckResult,
} from "./types";

function csrfHeaders(): Record<string, string> {
  const token = readCookie("motorscope_csrf");
  return token ? { "X-CSRF-Token": token } : {};
}

// Watchlist
export function getWatchlist(activeOnly: boolean = true): Promise<WatchlistEntryWithOpportunity[]> {
  return apiRequest<WatchlistEntryWithOpportunity[]>(
    `/watchlist?active_only=${activeOnly}`,
  );
}

export function createWatchlistEntry(
  opportunityId: string,
  notes?: string,
): Promise<WatchlistEntryPublic> {
  return apiRequest<WatchlistEntryPublic>(`/watchlist/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeaders(),
    },
    body: JSON.stringify({ opportunity_id: opportunityId, notes }),
  });
}

// Inspections
export function getInspections(watchlistEntryId: string): Promise<InspectionWithDetails[]> {
  return apiRequest<InspectionWithDetails[]>(`/inspections/?watchlist_entry_id=${watchlistEntryId}`);
}

export function createInspection(
  watchlistEntryId: string,
  inspectorName?: string,
  scheduledAt?: string,
): Promise<InspectionPublic> {
  return apiRequest<InspectionPublic>(`/inspections/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeaders(),
    },
    body: JSON.stringify({
      watchlist_entry_id: watchlistEntryId,
      inspector_name: inspectorName,
      scheduled_at: scheduledAt,
    }),
  });
}

export function updateInspectionStatus(
  inspectionId: string,
  status: InspectionStatus,
): Promise<InspectionPublic> {
  return apiRequest<InspectionPublic>(`/inspections/${inspectionId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeaders(),
    },
    body: JSON.stringify({ status }),
  });
}

// Checks
export function addInspectionCheck(
  inspectionId: string,
  category: string,
  name: string,
  description?: string,
): Promise<InspectionCheckPublic> {
  return apiRequest<InspectionCheckPublic>(`/inspections/${inspectionId}/checks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeaders(),
    },
    body: JSON.stringify({ category, name, description }),
  });
}

export function updateCheckResult(
  checkId: string,
  result: CheckResult,
  notes?: string,
): Promise<InspectionCheckPublic> {
  return apiRequest<InspectionCheckPublic>(`/inspections/checks/${checkId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeaders(),
    },
    body: JSON.stringify({ result, notes }),
  });
}

// Files
export function getInspectionFiles(inspectionId: string): Promise<FileAttachmentPublic[]> {
  return apiRequest<FileAttachmentPublic[]>(`/files/inspections/${inspectionId}`);
}

export async function uploadInspectionFile(
  inspectionId: string,
  file: File,
): Promise<FileAttachmentPublic> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`/api/v1/files/inspections/${inspectionId}`, {
    method: "POST",
    headers: csrfHeaders(),
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Failed to upload file");
  }

  return res.json() as Promise<FileAttachmentPublic>;
}
