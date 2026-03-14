import { API_BASE_URL } from "../api";
import { apiRequest } from "../queryClient";
import type {
  Contract,
  ContractChatRequest,
  ContractChatResponse,
  ContractUploadResponse,
} from "../types/contract";
import { getAccessToken } from "./token";

export async function getContracts(): Promise<Contract[]> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/contracts`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) throw new Error(`Failed to fetch contracts: ${response.status}`);
  return response.json();
}

export async function getContract(id: string): Promise<Contract> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/contracts/${id}`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) throw new Error(`Failed to fetch contract: ${response.status}`);
  return response.json();
}

export async function uploadContract(file: File): Promise<ContractUploadResponse> {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/contracts/upload`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to upload contract: ${response.status}`);
  }

  return response.json();
}

export interface BulkUploadResponse {
  contracts: Contract[];
  failedUploads: { fileName: string; error: string }[];
  message: string;
}

export async function uploadContractsBulk(files: File[]): Promise<BulkUploadResponse> {
  const token = getAccessToken();
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch(`${API_BASE_URL}/contracts/upload-bulk`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to upload contracts: ${response.status}`);
  }

  return response.json();
}

export async function seedSyntheticContract(): Promise<ContractUploadResponse> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/contracts/seed`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to seed synthetic contract: ${response.status}`);
  }

  return response.json();
}

export async function deleteContract(id: string): Promise<void> {
  await apiRequest("DELETE", `${API_BASE_URL}/contracts/${id}`);
}

export async function reprocessContract(id: string): Promise<ContractUploadResponse> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/contracts/${id}/reprocess`, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to reprocess contract: ${response.status}`);
  }

  return response.json();
}

export async function chatWithContract(
  contractId: string,
  payload: ContractChatRequest,
): Promise<ContractChatResponse> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/contracts/${contractId}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to chat with contract: ${response.status}`);
  }

  return response.json();
}



