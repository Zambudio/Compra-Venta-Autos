import { apiRequest } from "@/lib/api";

export type Source = {
  key: string;
  name: string;
  provider_kind: string;
  is_active: boolean;
  is_automatable: boolean;
};

export type SourceHealth = {
  source_key: string;
  healthy: boolean;
  detail: string;
  checked_at: string;
};

export async function getSources(): Promise<Source[]> {
  const res = await apiRequest<Source[]>('/sources');
  return res;
}

export async function updateSource(key: string, is_active: boolean): Promise<Source> {
  const res = await apiRequest<Source>(`/sources/${key}`, {
    method: 'PATCH',
    body: JSON.stringify({ is_active }),
  });
  return res;
}

export async function checkSourceHealth(key: string): Promise<SourceHealth> {
  const res = await apiRequest<SourceHealth>(`/sources/${key}/health`);
  return res;
}
