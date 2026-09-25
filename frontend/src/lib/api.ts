// API client — calls the FastAPI backend (Render)
// In dev: http://localhost:8000
// In prod: set NEXT_PUBLIC_API_URL in Vercel environment variables

import type {
  RegimeData,
  ForecastData,
  DistrictForecast,
  ApiResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    next: { revalidate: 1800 }, // ISR: revalidate every 30 min
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  const json: ApiResponse<T> = await res.json();
  return json.data;
}

export async function getRegime(date: string, leadH: number): Promise<RegimeData> {
  return apiFetch<RegimeData>(`/api/regime?date=${date}&lead_h=${leadH}`);
}

export async function getForecast(date: string, leadH: number): Promise<ForecastData> {
  return apiFetch<ForecastData>(`/api/forecast?date=${date}&lead_h=${leadH}`);
}

export async function getDistricts(
  date: string,
  leadH: number,
): Promise<DistrictForecast[]> {
  return apiFetch<DistrictForecast[]>(
    `/api/districts?date=${date}&lead_h=${leadH}`,
  );
}
