import { API_BASE_URL } from "../api";
import type { FormalAuditRun, Project, TruthVerificationRun } from "../types/project";
import { getAccessToken } from "./token";

async function authedFetch(path: string, init?: RequestInit) {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

export function listProjects(): Promise<Project[]> {
  return authedFetch("/projects");
}

export function ensureDefaultProject(): Promise<Project> {
  return authedFetch("/projects/ensure-default", { method: "POST" });
}

export function verifyProject(projectId: string, batchRunId?: string): Promise<TruthVerificationRun> {
  return authedFetch(`/projects/${projectId}/verify`, {
    method: "POST",
    body: JSON.stringify({ batchRunId }),
  });
}

export function createFormalAuditRun(
  projectId: string,
  payload: { batchRunId?: string; verificationRunId?: string }
): Promise<FormalAuditRun> {
  return authedFetch(`/projects/${projectId}/audit-runs`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createProject(payload: { name: string; description?: string; payerScope?: string }): Promise<Project> {
  return authedFetch("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
