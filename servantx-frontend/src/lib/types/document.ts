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
  notes_payload?: NotesPayload | string;
  appeal_status?: 'none' | 'identified' | 'drafted' | 'filed' | 'under_review' | 'approved' | 'partial' | 'denied';
  appeal_letter?: string;
  recovered_amount?: number | null;
  appeal_filed_at?: string | null;
  appeal_updated_at?: string | null;
}

export interface PricingEngineResult {
  engine: string;
  method?: string;
  expected_payment: number;
  actual_paid: number;
  variance_amount: number;
  variance_percent: number;
  confidence_score: number;
  rate_source: string;
  errors?: string[];
  ai_reasoning?: string;
}

export interface NotesPayload {
  pricing_comparison?: PricingEngineResult[];
  engines_run?: string[];
  pricing_mode?: string;
  [key: string]: unknown;
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
  appeal_status?: string;
}

export interface PaginatedDocumentsResponse {
  items: Document[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface ROIPayerSummary {
  payer: string;
  claims: number;
  identified: number;
  recovered: number;
  rate: number;
}

export interface ROIStatusSummary {
  appeal_status: string;
  count: number;
  identified: number;
  recovered: number;
}

export interface ROISummary {
  identified_total: number;
  recovered_total: number;
  recovery_rate: number;
  total_claims_processed: number;
  total_flagged: number;
  flag_rate: number;
  by_status: ROIStatusSummary[];
  by_payer: ROIPayerSummary[];
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



