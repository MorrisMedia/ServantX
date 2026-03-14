import { API_BASE_URL } from "../api";
import type { AnalysisPattern, AnalysisSummary, CoverageReport } from "../types/audit";
import { getAccessToken } from "./token";

export async function getAnalysisSummary(batchId?: string): Promise<AnalysisSummary> {
  const token = getAccessToken();
  const params = new URLSearchParams();
  if (batchId) params.append("batchId", batchId);
  const qs = params.toString();
  const url = `${API_BASE_URL}/analysis${qs ? `?${qs}` : ""}`;

  const response = await fetch(url, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to fetch analysis summary: ${response.status}`);
  }
  return response.json();
}

export async function getAnalysisPatterns(batchId?: string): Promise<AnalysisPattern[]> {
  const token = getAccessToken();
  const params = new URLSearchParams();
  if (batchId) params.append("batchId", batchId);
  const qs = params.toString();
  const url = `${API_BASE_URL}/analysis/patterns${qs ? `?${qs}` : ""}`;

  const response = await fetch(url, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to fetch analysis patterns: ${response.status}`);
  }
  return response.json();
}

export async function getCoverageReport(batchId?: string): Promise<CoverageReport> {
  const token = getAccessToken();
  const params = new URLSearchParams();
  if (batchId) params.append("batchId", batchId);
  const qs = params.toString();
  const url = `${API_BASE_URL}/analysis/coverage${qs ? `?${qs}` : ""}`;

  const response = await fetch(url, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to fetch coverage report: ${response.status}`);
  }
  return response.json();
}
