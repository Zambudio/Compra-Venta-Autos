import { apiRequest, readCookie } from "@/lib/api";
import type {
  ConfirmMatchResponse,
  MarketEstimate,
  MatchCandidatePage,
  MatchCandidateStatus,
  RejectMatchResponse,
  VehicleDetail,
  VehicleHistoryMetrics,
  VehiclePage,
} from "@/features/vehicles/types";

function csrfHeaders(): Record<string, string> {
  const token = readCookie("motorscope_csrf");
  return token ? { "X-CSRF-Token": token } : {};
}

export function getVehicles(params?: {
  page?: number | undefined;
  pageSize?: number | undefined;
  brand?: string | undefined;
  model?: string | undefined;
}): Promise<VehiclePage> {
  const q = new URLSearchParams();
  if (params?.page) q.set("page", String(params.page));
  if (params?.pageSize) q.set("page_size", String(params.pageSize));
  if (params?.brand) q.set("brand", params.brand);
  if (params?.model) q.set("model", params.model);
  const query = q.toString();
  return apiRequest<VehiclePage>(`/vehicles${query ? `?${query}` : ""}`);
}

export function getVehicle(vehicleId: string): Promise<VehicleDetail> {
  return apiRequest<VehicleDetail>(`/vehicles/${vehicleId}`);
}

export function getVehicleHistory(
  vehicleId: string,
): Promise<VehicleHistoryMetrics> {
  return apiRequest<VehicleHistoryMetrics>(`/vehicles/${vehicleId}/history`);
}

export function computeVehicleMarketEstimate(
  vehicleId: string,
  minComparables: number = 3,
): Promise<MarketEstimate> {
  return apiRequest<MarketEstimate>(
    `/vehicles/${vehicleId}/market-estimate?min_comparables=${minComparables}`,
    {
      method: "POST",
      headers: csrfHeaders(),
    },
  );
}

export function getMatchCandidates(
  status: MatchCandidateStatus = "PENDING",
  page: number = 1,
  pageSize: number = 20,
): Promise<MatchCandidatePage> {
  const q = new URLSearchParams({
    status,
    page: String(page),
    page_size: String(pageSize),
  });
  return apiRequest<MatchCandidatePage>(`/match-candidates?${q.toString()}`);
}

export function confirmMatchCandidate(
  candidateId: string,
): Promise<ConfirmMatchResponse> {
  return apiRequest<ConfirmMatchResponse>(
    `/match-candidates/${candidateId}/confirm`,
    {
      method: "POST",
      headers: csrfHeaders(),
    },
  );
}

export function rejectMatchCandidate(
  candidateId: string,
): Promise<RejectMatchResponse> {
  return apiRequest<RejectMatchResponse>(
    `/match-candidates/${candidateId}/reject`,
    {
      method: "POST",
      headers: csrfHeaders(),
    },
  );
}

export function generateMatchCandidates(): Promise<{
  created_candidates: number;
}> {
  return apiRequest<{ created_candidates: number }>(
    "/match-candidates/generate",
    {
      method: "POST",
      headers: csrfHeaders(),
    },
  );
}
