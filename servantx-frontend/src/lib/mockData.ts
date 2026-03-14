import { Document, DocumentStatus, DocumentStats } from "./types/document";
import { BillingRecord } from "./types/receipt";
import { Contract } from "./types/contract";

// Mock Documents
export const mockDocuments: Document[] = [
  {
    id: "doc-1",
    receiptId: "rec-1",
    status: DocumentStatus.SUCCEEDED,
    amount: 1250.50,
    createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    submittedAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
    contractId: "contract-1",
    rulesApplied: ["rule-1", "rule-2"],
    hospitalId: "hosp-1",
    notes: "Payment processed successfully",
  },
  {
    id: "doc-2",
    receiptId: "rec-2",
    status: DocumentStatus.IN_PROGRESS,
    amount: 850.25,
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    contractId: "contract-1",
    rulesApplied: ["rule-1"],
    hospitalId: "hosp-1",
  },
  {
    id: "doc-3",
    receiptId: "rec-3",
    status: DocumentStatus.NOT_SUBMITTED,
    amount: 2100.75,
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    contractId: "contract-1",
    hospitalId: "hosp-1",
  },
  {
    id: "doc-4",
    receiptId: "rec-4",
    status: DocumentStatus.FAILED,
    amount: 450.00,
    createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
    submittedAt: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
    contractId: "contract-1",
    hospitalId: "hosp-1",
    notes: "Failed to process payment - invalid account details",
  },
  {
    id: "doc-5",
    receiptId: "rec-5",
    status: DocumentStatus.SUCCEEDED,
    amount: 3200.00,
    createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
    submittedAt: new Date(Date.now() - 9 * 24 * 60 * 60 * 1000).toISOString(),
    contractId: "contract-1",
    rulesApplied: ["rule-1", "rule-2", "rule-3"],
    hospitalId: "hosp-1",
  },
];

// Mock Billing Records
export const mockBillingRecords: BillingRecord[] = [
  {
    id: "rec-1",
    hospitalId: "hosp-1",
    hasDifference: true,
    amount: 1250.50,
    uploadedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    documentId: "doc-1",
    fileName: "receipt_2024_01_15.pdf",
    fileSize: 245678,
    status: "processed",
  },
  {
    id: "rec-2",
    hospitalId: "hosp-1",
    hasDifference: true,
    amount: 850.25,
    uploadedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    documentId: "doc-2",
    fileName: "receipt_2024_01_17.pdf",
    fileSize: 189234,
    status: "processed",
  },
  {
    id: "rec-3",
    hospitalId: "hosp-1",
    hasDifference: true,
    amount: 2100.75,
    uploadedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    documentId: "doc-3",
    fileName: "receipt_2024_01_18.pdf",
    fileSize: 312456,
    status: "processed",
  },
  {
    id: "rec-4",
    hospitalId: "hosp-1",
    hasDifference: true,
    amount: 450.00,
    uploadedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    documentId: "doc-4",
    fileName: "receipt_2024_01_13.pdf",
    fileSize: 156789,
    status: "processed",
  },
  {
    id: "rec-5",
    hospitalId: "hosp-1",
    hasDifference: true,
    amount: 3200.00,
    uploadedAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    documentId: "doc-5",
    fileName: "receipt_2024_01_10.pdf",
    fileSize: 423567,
    status: "processed",
  },
  {
    id: "rec-6",
    hospitalId: "hosp-1",
    hasDifference: false,
    amount: 675.50,
    uploadedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    fileName: "receipt_2024_01_19.pdf",
    fileSize: 198765,
    status: "processed",
  },
  {
    id: "rec-7",
    hospitalId: "hosp-1",
    hasDifference: false,
    amount: 920.25,
    uploadedAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
    fileName: "receipt_2024_01_16.pdf",
    fileSize: 234567,
    status: "processed",
  },
];

// Mock Contract
export const mockContract: Contract | null = {
  id: "contract-1",
  hospitalId: "hosp-1",
  name: "Main Service Contract 2024",
  fileName: "service_contract_2024.pdf",
  fileSize: 1024567,
  uploadedAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  status: "processed",
  rulesExtracted: 5,
  notes: "Contract processed successfully. 5 rules extracted.",
};

// Mock Document Stats
export const mockDocumentStats: DocumentStats = {
  total: mockDocuments.length,
  notSubmitted: mockDocuments.filter(d => d.status === DocumentStatus.NOT_SUBMITTED).length,
  inProgress: mockDocuments.filter(d => d.status === DocumentStatus.IN_PROGRESS).length,
  succeeded: mockDocuments.filter(d => d.status === DocumentStatus.SUCCEEDED).length,
  failed: mockDocuments.filter(d => d.status === DocumentStatus.FAILED).length,
  totalRevenue: mockDocuments
    .filter(d => d.status === DocumentStatus.SUCCEEDED)
    .reduce((sum, d) => sum + d.amount, 0),
};

// Helper function to get mock document by ID
export function getMockDocument(id: string): Document | undefined {
  return mockDocuments.find(doc => doc.id === id);
}

// Helper function to get mock billing record by ID
export function getMockBillingRecord(id: string): BillingRecord | undefined {
  return mockBillingRecords.find(rec => rec.id === id);
}

// Backward-compatible aliases during rename transition.
export const mockReceipts = mockBillingRecords;
export const getMockReceipt = getMockBillingRecord;

// Helper function to get mock contract
export function getMockContract(): Contract | null {
  return mockContract;
}

