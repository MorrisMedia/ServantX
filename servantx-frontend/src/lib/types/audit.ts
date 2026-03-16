import type { Document } from "./document";


export type AuditPayerScope = "CONTRACT_AUDIT" | "MEDICARE" | "TX_MEDICAID_FFS";

export interface BatchUploadRequest {
  files: File[];
  payerScope?: AuditPayerScope;
}

export interface BatchRun {
  id: string;
  hospitalId: string;
  status: string;
  payerScope: string;
  sourceFileCount: number;
  claimDocumentCount: number;
  processedClaimCount: number;
  failedClaimCount: number;
  executiveSummary?: string;
  reconciliationJson?: Record<string, unknown>;
  startedAt?: string;
  finishedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface BatchUploadResponse {
  batch: BatchRun;
  filesQueued: number;
  message: string;
}

export interface AnalysisPattern {
  payerKey?: string;
  cptHcpcs?: string;
  modifier?: string;
  placeOfService?: string;
  localityCode?: string;
  claimCount: number;
  totalVariance: number;
  confidence: number;
}

export interface AnalysisSummary {
  totalClaims: number;
  totalServiceLines: number;
  totalPaid: number;
  totalExpected: number;
  totalVariance: number;
  claimsFlagged: number;
  topCpts: AnalysisPattern[];
  topProviders: { providerId: string; totalVariance: number }[];
  topPatterns: AnalysisPattern[];
}

export interface CoverageReport {
  lineCount: number;
  matchedRateCount: number;
  knownLocalityCount: number;
  matchedRatePercent: number;
  knownLocalityPercent: number;
  allowedMismatchCount: number;
  topMissingRateCpts: Array<{ cptHcpcs: string; count: number }>;
}

export interface AppealBuildRequest {
  batchId: string;
  payerKey?: string;
  minimumVariance?: number;
}

export interface AppealBuildResponse {
  batchId: string;
  packet: Record<string, unknown>;
  message: string;
}

export interface RateStatus {
  versions: Array<{
    id: string;
    payerKey: string;
    versionLabel: string;
    effectiveStart?: string;
    effectiveEnd?: string;
    sourceUrl: string;
    importedAt: string;
    rowCount: number;
    sha256: string;
  }>;
  coverage: Record<string, number>;
}

export interface BatchDocumentsResponse {
  items: Document[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}
