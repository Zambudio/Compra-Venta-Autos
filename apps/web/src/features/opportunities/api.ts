import { apiRequest, readCookie } from "@/lib/api";
import type {
  OpportunityFilterParams,
  OpportunityPage,
  OpportunityRead,
  OpportunityStatus,
} from "@/features/opportunities/types";

function csrfHeaders(): Record<string, string> {
  const token = readCookie("motorscope_csrf");
  return token ? { "X-CSRF-Token": token } : {};
}

export function getOpportunities(
  params?: OpportunityFilterParams,
): Promise<OpportunityPage> {
  const q = new URLSearchParams();
  if (params?.page) q.set("page", String(params.page));
  if (params?.pageSize) q.set("page_size", String(params.pageSize));
  if (params?.status) q.set("status", params.status);
  if (params?.min_score !== undefined)
    q.set("min_score", String(params.min_score));
  if (params?.min_roi !== undefined) q.set("min_roi", String(params.min_roi));
  if (params?.brand) q.set("brand", params.brand);
  const query = q.toString();
  return apiRequest<OpportunityPage>(
    `/opportunities${query ? `?${query}` : ""}`,
  );
}

export function getOpportunity(
  opportunityId: string,
): Promise<OpportunityRead> {
  return apiRequest<OpportunityRead>(`/opportunities/${opportunityId}`);
}

export function evaluateListing(listingId: string): Promise<OpportunityRead> {
  return apiRequest<OpportunityRead>(
    `/opportunities/evaluate/listing/${listingId}`,
    {
      method: "POST",
      headers: csrfHeaders(),
    },
  );
}

export function evaluateVehicle(vehicleId: string): Promise<OpportunityRead> {
  return apiRequest<OpportunityRead>(
    `/opportunities/evaluate/vehicle/${vehicleId}`,
    {
      method: "POST",
      headers: csrfHeaders(),
    },
  );
}

export function updateOpportunityStatus(
  opportunityId: string,
  status: OpportunityStatus,
  notes?: string,
): Promise<OpportunityRead> {
  return apiRequest<OpportunityRead>(`/opportunities/${opportunityId}/status`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeaders(),
    },
    body: JSON.stringify({ status, notes: notes ?? null }),
  });
}
