import { apiRequest, readCookie } from "@/lib/api";

export type Source = {
  key: string;
  name: string;
  provider_kind: string;
  is_active: boolean;
  is_automatable: boolean;
  enabled: boolean;
  config: Record<string, unknown>;
  last_sync: string | null;
  sync_error: string | null;
  health: "ok" | "error" | "disabled";
  latest_review?: {
    acquisition_method: string;
    automated_allowed: boolean;
    authentication_required: string;
    rate_limit: string | null;
    terms_url: string | null;
    checked_at: string;
    notes: string;
  } | null;
};

export type SourceConfiguration = {
  key: string;
  enabled: boolean;
  config: Record<string, unknown>;
  last_sync: string | null;
  sync_error: string | null;
  updated_at: string;
};

export type SourceHealth = {
  source_key: string;
  healthy: boolean;
  detail: string;
  checked_at: string;
};

export type SyncRun = {
  id: string;
  source_key: string;
  status: "PENDING" | "RUNNING" | "SUCCESS" | "PARTIAL" | "FAILED";
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

export async function getSources(): Promise<Source[]> {
  const res = await apiRequest<Source[]>("/sources");
  return res;
}

function csrfHeaders(): Record<string, string> {
  const token = readCookie("motorscope_csrf");
  return token ? { "X-CSRF-Token": token } : {};
}

export async function updateSource(
  key: string,
  enabled: boolean,
): Promise<SourceConfiguration> {
  const res = await apiRequest<SourceConfiguration>(`/sources/${key}/config`, {
    method: "PATCH",
    headers: csrfHeaders(),
    body: JSON.stringify({ enabled }),
  });
  return res;
}

export async function checkSourceHealth(key: string): Promise<SourceHealth> {
  const res = await apiRequest<SourceHealth>(`/sources/${key}/health`);
  return res;
}

export async function syncSource(key: string): Promise<SyncRun> {
  return apiRequest<SyncRun>(`/sources/${key}/sync`, {
    method: "POST",
    headers: csrfHeaders(),
    body: JSON.stringify({}),
  });
}
