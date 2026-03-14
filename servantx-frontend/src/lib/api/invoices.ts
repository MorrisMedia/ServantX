import { API_BASE_URL } from "../api";
import type { Invoice, InvoiceFilters } from "../types/invoice";

export async function getInvoices(filters?: InvoiceFilters): Promise<Invoice[]> {
  const params = new URLSearchParams();
  if (filters?.dateFrom) params.append("dateFrom", filters.dateFrom);
  if (filters?.dateTo) params.append("dateTo", filters.dateTo);
  if (filters?.amountMin !== undefined) params.append("amountMin", filters.amountMin.toString());
  if (filters?.amountMax !== undefined) params.append("amountMax", filters.amountMax.toString());
  if (filters?.hospitalId) params.append("hospitalId", filters.hospitalId);
  if (filters?.payer) params.append("payer", filters.payer);
  if (filters?.status) {
    filters.status.forEach((s) => params.append("status", s));
  }
  if (filters?.sortBy) params.append("sortBy", filters.sortBy);
  if (filters?.sortOrder) params.append("sortOrder", filters.sortOrder);

  const queryString = params.toString();
  const url = `${API_BASE_URL}/invoices${queryString ? `?${queryString}` : ""}`;
  const response = await fetch(url, { credentials: "include" });
  if (!response.ok) throw new Error(`Failed to fetch invoices: ${response.status}`);
  return response.json();
}

export async function getInvoice(id: string): Promise<Invoice> {
  const response = await fetch(`${API_BASE_URL}/invoices/${id}`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error(`Failed to fetch invoice: ${response.status}`);
  return response.json();
}



