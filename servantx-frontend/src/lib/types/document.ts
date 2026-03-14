export enum DocumentStatus {
  NOT_SUBMITTED = "not_submitted",
  IN_PROGRESS = "in_progress",
  SUCCEEDED = "succeeded",
  FAILED = "failed",
  CANCELLED = "cancelled",
  DECLINED = "declined",
}

export interface Document {
  id: string;
  receiptId: string | null;
  name?: string;
  status: DocumentStatus;
  amount: number;
  createdAt: string;
  updatedAt: string;
  submittedAt?: string;
  contractId?: string;
  batchRunId?: string;
  documentRole?: string;
  parentDocumentId?: string;
  payerKey?: string;
  dosStart?: string;
  dosEnd?: string;
  billingNpi?: string;
  renderingNpi?: string;
  facilityNpi?: string;
  sourceFileName?: string;
  sourceFilePath?: string;
  rulesApplied?: string[];
  hospitalId: string;
  projectId?: string;
  notes?: string;
  hasUnderpayment?: boolean;
  contractAmount?: number;
  receiptAmount?: number;
  underpaymentAmount?: number;
  reasoning?: string;
  isBulkDownloaded?: boolean;
  parsedData?: Record<string, unknown>;
  findings?: Array<Record<string, unknown>>;
  repricingSummary?: Record<string, unknown>;
}

export interface DocumentFilters {
  status?: DocumentStatus[];
  dateFrom?: string;
  dateTo?: string;
  amountMin?: number;
  amountMax?: number;
  hospitalId?: string;
  contractId?: string;
  receiptId?: string;
  search?: string;
  sortBy?: "createdAt" | "amount" | "status" | "updatedAt";
  sortOrder?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface PaginatedDocumentsResponse {
  items: Document[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface DocumentStats {
  total: number;
  notSubmitted: number;
  inProgress: number;
  succeeded: number;
  failed?: number;
  cancelled?: number;
  declined?: number;
  totalRevenue: number;
  totalUnderpayment?: number;
}



