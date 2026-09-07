import { apiRequest, readCookie } from "@/lib/api";
import type {
  Engine,
  EngineVariant,
  KnownIssue,
  KnownIssuePage,
  Manufacturer,
  ReliabilityLookupResponse,
  TransmissionSpec,
  VehicleClassificationPage,
  VehicleGeneration,
  VehicleMitigation,
  VehicleModel,
} from "./types";

function csrfHeaders(): Record<string, string> {
  const token = readCookie("motorscope_csrf");
  return token ? { "X-CSRF-Token": token } : {};
}

// --- Jerarquía técnica ---

export function getManufacturers(): Promise<Manufacturer[]> {
  return apiRequest<Manufacturer[]>("/knowledge/manufacturers");
}

export function getModels(manufacturerId?: string | undefined): Promise<VehicleModel[]> {
  const q = new URLSearchParams();
  if (manufacturerId) q.set("manufacturer_id", manufacturerId);
  const query = q.toString();
  return apiRequest<VehicleModel[]>(`/knowledge/models${query ? `?${query}` : ""}`);
}

export function getGenerations(modelId?: string | undefined): Promise<VehicleGeneration[]> {
  const q = new URLSearchParams();
  if (modelId) q.set("model_id", modelId);
  const query = q.toString();
  return apiRequest<VehicleGeneration[]>(
    `/knowledge/generations${query ? `?${query}` : ""}`,
  );
}

export function getEngines(params?: {
  manufacturerId?: string | undefined;
  fuelType?: string | undefined;
} | undefined): Promise<Engine[]> {
  const q = new URLSearchParams();
  if (params?.manufacturerId) q.set("manufacturer_id", params.manufacturerId);
  if (params?.fuelType) q.set("fuel_type", params.fuelType);
  const query = q.toString();
  return apiRequest<Engine[]>(`/knowledge/engines${query ? `?${query}` : ""}`);
}

export function getEngineVariants(engineId?: string | undefined): Promise<EngineVariant[]> {
  const q = new URLSearchParams();
  if (engineId) q.set("engine_id", engineId);
  const query = q.toString();
  return apiRequest<EngineVariant[]>(
    `/knowledge/engine-variants${query ? `?${query}` : ""}`,
  );
}

export function getTransmissions(): Promise<TransmissionSpec[]> {
  return apiRequest<TransmissionSpec[]>("/knowledge/transmissions");
}

// --- Problemas Conocidos ---

export function getKnownIssues(params?: {
  component?: string | undefined;
  severity?: string | undefined;
  status?: string | undefined;
  page?: number | undefined;
  pageSize?: number | undefined;
} | undefined): Promise<KnownIssuePage> {
  const q = new URLSearchParams();
  if (params?.component) q.set("component", params.component);
  if (params?.severity) q.set("severity", params.severity);
  if (params?.status) q.set("status", params.status);
  if (params?.page != null) q.set("page", String(params.page));
  if (params?.pageSize != null) q.set("page_size", String(params.pageSize));
  const query = q.toString();
  return apiRequest<KnownIssuePage>(`/knowledge/issues${query ? `?${query}` : ""}`);
}

export function getKnownIssue(id: string): Promise<KnownIssue> {
  return apiRequest<KnownIssue>(`/knowledge/issues/${id}`);
}

// --- Clasificaciones ---

export function getClassifications(params?: {
  status?: string | undefined;
  targetType?: string | undefined;
  page?: number | undefined;
  pageSize?: number | undefined;
} | undefined): Promise<VehicleClassificationPage> {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.targetType) q.set("target_type", params.targetType);
  if (params?.page != null) q.set("page", String(params.page));
  if (params?.pageSize != null) q.set("page_size", String(params.pageSize));
  const query = q.toString();
  return apiRequest<VehicleClassificationPage>(
    `/knowledge/classifications${query ? `?${query}` : ""}`,
  );
}

// --- Lookup de Fiabilidad y Mitigaciones ---

export function lookupVehicleReliability(params: {
  brand: string;
  model: string;
  year?: number | null | undefined;
  fuelType?: string | null | undefined;
  engineCode?: string | null | undefined;
}): Promise<ReliabilityLookupResponse> {
  const q = new URLSearchParams();
  q.set("brand", params.brand);
  q.set("model", params.model);
  if (params.year != null) q.set("year", String(params.year));
  if (params.fuelType) q.set("fuel_type", params.fuelType);
  if (params.engineCode) q.set("engine_code", params.engineCode);
  return apiRequest<ReliabilityLookupResponse>(
    `/knowledge/reliability-lookup?${q.toString()}`,
  );
}

export function getVehicleMitigations(vehicleId: string): Promise<VehicleMitigation[]> {
  return apiRequest<VehicleMitigation[]>(
    `/knowledge/vehicles/${vehicleId}/mitigations`,
  );
}

export function addVehicleMitigation(data: {
  vehicle_id: string;
  known_issue_id: string;
  mitigation_type: string;
  description: string;
  applied_at?: string | undefined;
}): Promise<VehicleMitigation> {
  return apiRequest<VehicleMitigation>("/knowledge/mitigations", {
    method: "POST",
    headers: csrfHeaders(),
    body: JSON.stringify(data),
  });
}
