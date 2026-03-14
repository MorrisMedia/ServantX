import { API_BASE_URL } from "../api";
import type { RateStatus } from "../types/audit";
import { getAccessToken } from "./token";

export async function getRatesStatus(): Promise<RateStatus> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/admin/rates/status`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to fetch rates status: ${response.status}`);
  }
  return response.json();
}
