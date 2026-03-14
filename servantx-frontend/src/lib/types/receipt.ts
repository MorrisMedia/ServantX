export interface BillingRecord {
  id: string;
  hospitalId: string;
  hasDifference: boolean;
  amount: number;
  uploadedAt: string;
  documentId?: string; // if hasDifference = true
  fileName: string;
  fileSize?: number;
  fileUrl?: string;
  status?: "pending" | "processing" | "processed" | "error";
}

export interface BillingRecordUploadResponse {
  // Backend currently returns this property name.
  receipt: BillingRecord;
  document?: {
    id: string;
    status: string;
  };
}

export interface BillingRecordFilters {
  hasDifference?: boolean;
  dateFrom?: string;
  dateTo?: string;
  status?: string[];
  hospitalId?: string;
  search?: string;
  sortBy?: "uploadedAt" | "amount" | "fileName";
  sortOrder?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface PaginatedBillingRecordsResponse {
  items: BillingRecord[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

// Backward-compatible aliases during rename transition.
export type Receipt = BillingRecord;
export type ReceiptUploadResponse = BillingRecordUploadResponse;
export type ReceiptFilters = BillingRecordFilters;
export type PaginatedReceiptsResponse = PaginatedBillingRecordsResponse;



