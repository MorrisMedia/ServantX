export interface ProjectWorkspaceSummary {
  duckdbPath?: string;
  documentCount?: number;
  totalUnderpayment?: number;
  tables?: string[];
}

export interface Project {
  id: string;
  hospitalId: string;
  name: string;
  slug: string;
  description?: string;
  status: string;
  payerScope?: string;
  workspaceDuckdbPath?: string;
  storagePrefix?: string;
  workspaceSummary?: ProjectWorkspaceSummary;
  createdAt: string;
  updatedAt: string;
}

export interface TruthVerificationRun {
  id: string;
  projectId: string;
  batchRunId?: string;
  status: string;
  verificationSummary: Record<string, unknown>;
  createdAt: string;
  completedAt?: string;
}

export interface FormalAuditRun {
  id: string;
  projectId: string;
  batchRunId?: string;
  verificationRunId?: string;
  status: string;
  auditStandard: string;
  report: Record<string, unknown>;
  createdAt: string;
  completedAt?: string;
}
