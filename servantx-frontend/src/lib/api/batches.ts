import { API_BASE_URL } from "../api";
import type { BatchDocumentsResponse, BatchRun, BatchUploadResponse, BatchUploadRequest } from "../types/audit";
import { getAccessToken } from "./token";

export async function upload835Batch(payload: BatchUploadRequest): Promise<BatchUploadResponse> {
  const token = getAccessToken();
  const formData = new FormData();
  payload.files.forEach((file) => formData.append("files", file));
  if (payload.payerScope) formData.append("payerScope", payload.payerScope);
  if (payload.projectId) formData.append("project_id", payload.projectId);

  const response = await fetch(`${API_BASE_URL}/batches/upload-835`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to upload 835 batch: ${response.status}`);
  }
  return response.json();
}

export async function getBatchStatus(batchId: string): Promise<BatchRun> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/batches/${batchId}/status`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to fetch batch status: ${response.status}`);
  }
  return response.json();
}

export async function getBatchDocuments(batchId: string): Promise<BatchDocumentsResponse> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/batches/${batchId}/documents`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to fetch batch documents: ${response.status}`);
  }
  return response.json();
}
