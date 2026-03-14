import { API_BASE_URL } from "../api";
import { apiRequest } from "../queryClient";
import type {
  BillingRecord,
  BillingRecordUploadResponse,
  BillingRecordFilters,
  PaginatedBillingRecordsResponse,
} from "../types/receipt";
import { getAccessToken } from "./token";

const USE_MOCK_DATA = false;

export interface BillingRecordsZipUploadResponse {
  billingRecords: BillingRecord[];
  // Backward-compatible field for callers still reading `receipts`.
  receipts: BillingRecord[];
  message?: string;
  errors?: string[];
}

export async function getBillingRecords(
  filters?: BillingRecordFilters
): Promise<PaginatedBillingRecordsResponse> {
  const token = getAccessToken();
  const params = new URLSearchParams();
  if (filters?.hasDifference !== undefined) params.append("hasDifference", filters.hasDifference.toString());
  if (filters?.dateFrom) params.append("dateFrom", filters.dateFrom);
  if (filters?.dateTo) params.append("dateTo", filters.dateTo);
  if (filters?.status) {
    filters.status.forEach((s) => params.append("status", s));
  }
  if (filters?.hospitalId) params.append("hospitalId", filters.hospitalId);
  if (filters?.search) params.append("search", filters.search);
  if (filters?.sortBy) params.append("sortBy", filters.sortBy);
  if (filters?.sortOrder) params.append("sortOrder", filters.sortOrder);
  if (filters?.limit) params.append("limit", filters.limit.toString());
  if (filters?.offset !== undefined) params.append("offset", filters.offset.toString());

  const queryString = params.toString();
  const url = `${API_BASE_URL}/receipts${queryString ? `?${queryString}` : ""}`;
  const response = await fetch(url, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) throw new Error(`Failed to fetch billing records: ${response.status}`);
  return response.json();
}

export async function getBillingRecord(id: string): Promise<BillingRecord> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/receipts/${id}`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) throw new Error(`Failed to fetch billing record: ${response.status}`);
  return response.json();
}

export async function uploadBillingRecord(file: File): Promise<BillingRecordUploadResponse> {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/receipts/upload`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to upload billing record: ${response.status}`);
  }

  return response.json();
}

export async function uploadBillingRecordsBulk(
  files: File[]
): Promise<BillingRecordUploadResponse[]> {
  const token = getAccessToken();
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch(`${API_BASE_URL}/receipts/upload/bulk`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to upload billing records: ${response.status}`);
  }

  return response.json();
}

export async function uploadBillingRecordsZip(
  file: File
): Promise<BillingRecordsZipUploadResponse> {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/receipts/upload/zip`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to upload zip file: ${response.status}`);
  }

  const data = await response.json();
  const billingRecords = (data.billingRecords || data.receipts || []) as BillingRecord[];
  return {
    ...data,
    billingRecords,
    receipts: billingRecords,
  };
}

export async function deleteBillingRecord(id: string): Promise<void> {
  await apiRequest("DELETE", `${API_BASE_URL}/receipts/${id}`);
}

export async function scanBillingRecordForIssues(
  id: string
): Promise<{ document: any; message: string }> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/receipts/${id}/scan`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to scan billing record: ${response.status}`);
  }

  return response.json();
}

// Backward-compatible aliases during rename transition.
export const getReceipts = getBillingRecords;
export const getReceipt = getBillingRecord;
export const uploadReceipt = uploadBillingRecord;
export const uploadReceiptsBulk = uploadBillingRecordsBulk;
export const uploadReceiptsZip = uploadBillingRecordsZip;
export const deleteReceipt = deleteBillingRecord;
export const scanReceiptForIssues = scanBillingRecordForIssues;



