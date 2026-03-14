export interface Contract {
  id: string;
  hospitalId: string;
  name: string;
  fileName: string;
  fileSize?: number;
  fileUrl?: string;
  uploadedAt: string;
  status: "pending" | "processing" | "processed" | "error";
  rulesExtracted?: number;
  notes?: string;
}

export interface ContractUploadResponse {
  contract: Contract;
  message?: string;
}

export interface ContractChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ContractChatRequest {
  question: string;
  includeWeb?: boolean;
  history?: ContractChatMessage[];
}

export interface ContractChatSource {
  sourceType: "contract" | "web";
  title: string;
  url?: string | null;
  snippet: string;
}

export interface ContractChatResponse {
  contractId: string;
  contractName: string;
  answer: string;
  usedWeb: boolean;
  sources: ContractChatSource[];
  disclaimer: string;
}



