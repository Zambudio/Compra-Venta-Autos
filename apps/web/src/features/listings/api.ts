import { apiRequest, readCookie } from "@/lib/api";
import type {
  Listing,
  ListingDetail,
  ListingFilters,
  ListingPage,
  ManualListingInput,
  Source,
  SyncRun,
} from "@/features/listings/types";

function buildQuery(filters: ListingFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      for (const entry of value) params.append(key, String(entry));
    } else {
      params.set(key, String(value));
    }
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function getListings(filters: ListingFilters): Promise<ListingPage> {
  return apiRequest<ListingPage>(`/listings${buildQuery(filters)}`);
}

export function getListing(id: string): Promise<ListingDetail> {
  return apiRequest<ListingDetail>(`/listings/${id}`);
}

export function getSources(): Promise<Source[]> {
  return apiRequest<Source[]>("/sources");
}

function csrfHeaders(): Record<string, string> {
  const token = readCookie("motorscope_csrf");
  return token ? { "X-CSRF-Token": token } : {};
}

export function syncSource(key: string): Promise<SyncRun> {
  return apiRequest<SyncRun>(`/sources/${key}/sync`, {
    method: "POST",
    headers: csrfHeaders(),
    body: JSON.stringify({}),
  });
}

export function createManualListing(
  input: ManualListingInput,
): Promise<Listing> {
  return apiRequest<Listing>("/listings/manual", {
    method: "POST",
    headers: csrfHeaders(),
    body: JSON.stringify(input),
  });
}
