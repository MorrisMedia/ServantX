import { API_BASE_URL } from "../api";
import { getMockDocument, mockDocumentStats } from "../mockData";
import type { Document, DocumentFilters, DocumentStats, PaginatedDocumentsResponse } from "../types/document";
import { getAccessToken } from "./token";

const USE_MOCK_DATA = false;

export async function getDocuments(filters?: DocumentFilters): Promise<PaginatedDocumentsResponse> {
  const token = getAccessToken();
  const params = new URLSearchParams();
  if (filters?.status) {
    filters.status.forEach((s) => params.append("status", s));
  }
  if (filters?.dateFrom) params.append("dateFrom", filters.dateFrom);
  if (filters?.dateTo) params.append("dateTo", filters.dateTo);
  if (filters?.amountMin !== undefined) params.append("amountMin", filters.amountMin.toString());
  if (filters?.amountMax !== undefined) params.append("amountMax", filters.amountMax.toString());
  if (filters?.hospitalId) params.append("hospitalId", filters.hospitalId);
  if ((filters as any)?.projectId) params.append("projectId", (filters as any).projectId);
  if (filters?.contractId) params.append("contractId", filters.contractId);
  if (filters?.receiptId) params.append("receiptId", filters.receiptId);
  if ((filters as any)?.projectId) params.append("projectId", (filters as any).projectId);
  if (filters?.search) params.append("search", filters.search);
  if (filters?.sortBy) params.append("sortBy", filters.sortBy);
  if (filters?.sortOrder) params.append("sortOrder", filters.sortOrder);
  if (filters?.limit) params.append("limit", filters.limit.toString());
  if (filters?.offset !== undefined) params.append("offset", filters.offset.toString());

  const queryString = params.toString();
  const url = `${API_BASE_URL}/documents${queryString ? `?${queryString}` : ""}`;
  const response = await fetch(url, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) throw new Error(`Failed to fetch documents: ${response.status}`);
  return response.json();
}

export async function getDocument(id: string): Promise<Document> {
  if (USE_MOCK_DATA) {
    await new Promise(resolve => setTimeout(resolve, 300));
    const doc = getMockDocument(id);
    if (!doc) throw new Error(`Document not found: ${id}`);
    return doc;
  }

  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/documents/${id}`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) throw new Error(`Failed to fetch document: ${response.status}`);
  return response.json();
}

export async function submitDocument(id: string): Promise<Document> {
  if (USE_MOCK_DATA) {
    await new Promise(resolve => setTimeout(resolve, 500));
    const doc = getMockDocument(id);
    if (!doc) throw new Error(`Document not found: ${id}`);
    return {
      ...doc,
      status: "in_progress" as any,
      submittedAt: new Date().toISOString(),
    };
  }

  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/documents/${id}/submit`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to submit document: ${response.status}`);
  }
  return response.json();
}

export async function getDocumentStats(filters?: DocumentFilters): Promise<DocumentStats> {
  if (USE_MOCK_DATA) {
    await new Promise(resolve => setTimeout(resolve, 200));
    return mockDocumentStats;
  }

  const token = getAccessToken();
  const params = new URLSearchParams();
  if (filters?.dateFrom) params.append("dateFrom", filters.dateFrom);
  if (filters?.dateTo) params.append("dateTo", filters.dateTo);
  if (filters?.hospitalId) params.append("hospitalId", filters.hospitalId);
  if ((filters as any)?.projectId) params.append("projectId", (filters as any).projectId);

  const queryString = params.toString();
  const url = `${API_BASE_URL}/documents/stats${queryString ? `?${queryString}` : ""}`;
  const response = await fetch(url, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) throw new Error(`Failed to fetch document stats: ${response.status}`);
  return response.json();
}

export interface DocumentUpdateData {
  name?: string;
  notes?: string;
  receiptAmount?: number;
  contractAmount?: number;
  underpaymentAmount?: number;
  status?: string;
}

export async function updateDocument(id: string, data: DocumentUpdateData): Promise<Document> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/documents/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to update document: ${response.status}`);
  }
  return response.json();
}

export async function markDocumentsBulkDownloaded(documentIds: string[]): Promise<{ success: boolean; count: number; message: string }> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/documents/bulk-download`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify({ documentIds }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to mark documents as bulk downloaded: ${response.status}`);
  }
  return response.json();
}



