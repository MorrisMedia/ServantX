import { API_BASE_URL } from "../api";
import type { AppealBuildRequest, AppealBuildResponse } from "../types/audit";
import { getAccessToken } from "./token";

export async function buildAppealPacket(payload: AppealBuildRequest): Promise<AppealBuildResponse> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/appeals/build`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to build appeal packet: ${response.status}`);
  }
  return response.json();
}
