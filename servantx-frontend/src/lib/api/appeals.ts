import { API_BASE_URL } from "../api";
import type { AppealBuildRequest, AppealBuildResponse } from "../types/audit";
import type { ROISummary } from "../types/document";
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

export interface GenerateAppealLetterResponse {
  letter: string;
  summary: string;
  appeal_status: string;
}

export async function generateAppealLetter(
  documentId: string,
  additionalContext?: string
): Promise<GenerateAppealLetterResponse> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/generate-appeal`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify({ additional_context: additionalContext }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to generate appeal letter: ${response.status}`);
  }
  return response.json();
}

export interface UpdateAppealStatusData {
  appeal_status?: string;
  recovered_amount?: number;
}

export async function updateAppealStatus(
  documentId: string,
  data: UpdateAppealStatusData
): Promise<{ appeal_status: string; recovered_amount?: number }> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/appeal`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to update appeal status: ${response.status}`);
  }
  return response.json();
}

export async function getROISummary(): Promise<ROISummary> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/analytics/roi`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) {
    if (response.status === 404 || response.status >= 500) {
      // Endpoint not live yet — return empty/zero data
      return {
        identified_total: 0,
        recovered_total: 0,
        recovery_rate: 0,
        total_claims_processed: 0,
        total_flagged: 0,
        flag_rate: 0,
        by_status: [],
        by_payer: [],
      };
    }
    const text = await response.text();
    throw new Error(text || `Failed to fetch ROI summary: ${response.status}`);
  }
  return response.json();
}
