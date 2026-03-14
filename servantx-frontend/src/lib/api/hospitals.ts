import { API_BASE_URL } from "../api";
import { apiRequest } from "../queryClient";
import type { Hospital, HospitalSettings } from "../types/hospital";

export async function getHospital(): Promise<Hospital> {
  const response = await fetch(`${API_BASE_URL}/hospitals/me`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error(`Failed to fetch hospital: ${response.status}`);
  return response.json();
}

export async function updateHospital(data: Partial<Hospital>): Promise<Hospital> {
  const response = await apiRequest("PATCH", `${API_BASE_URL}/hospitals/me`, data);
  return response.json();
}

export async function getHospitalSettings(): Promise<HospitalSettings> {
  const response = await fetch(`${API_BASE_URL}/hospitals/me/settings`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error(`Failed to fetch hospital settings: ${response.status}`);
  return response.json();
}

export async function updateHospitalSettings(
  settings: Partial<HospitalSettings>
): Promise<HospitalSettings> {
  const response = await apiRequest("PATCH", `${API_BASE_URL}/hospitals/me/settings`, settings);
  return response.json();
}



