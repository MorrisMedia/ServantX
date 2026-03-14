export interface Invoice {
  id: string;
  hospitalId: string;
  receiptId?: string;
  documentId?: string;
  invoiceNumber?: string;
  amount: number;
  date: string;
  payer?: string;
  status?: string;
  fileUrl?: string;
  createdAt: string;
}

export interface InvoiceFilters {
  dateFrom?: string;
  dateTo?: string;
  amountMin?: number;
  amountMax?: number;
  hospitalId?: string;
  payer?: string;
  status?: string[];
  sortBy?: "date" | "amount" | "invoiceNumber";
  sortOrder?: "asc" | "desc";
}



