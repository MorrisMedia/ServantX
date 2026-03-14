import { DocumentFilters, DocumentStatus } from "@/lib/types/document";
import { getThisMonthRange, getThisYearRange } from "@/lib/utils/date";
import { useState } from "react";
import { useLocation } from "wouter";

export function useDocumentFilters() {
  const [location, setLocation] = useLocation();
  const [filters, setFilters] = useState<DocumentFilters>(() => {
    const params = new URLSearchParams(window.location.search);
    const statusParam = params.get("status");
    const dateFrom = params.get("dateFrom") || undefined;
    const dateTo = params.get("dateTo") || undefined;
    const amountMin = params.get("amountMin") ? Number(params.get("amountMin")) : undefined;
    const amountMax = params.get("amountMax") ? Number(params.get("amountMax")) : undefined;
    const hospitalId = params.get("hospitalId") || undefined;
    const contractId = params.get("contractId") || undefined;
    const receiptId = params.get("receiptId") || undefined;
    const search = params.get("search") || undefined;
    const sortBy = (params.get("sortBy") as DocumentFilters["sortBy"]) || undefined;
    const sortOrder = (params.get("sortOrder") as DocumentFilters["sortOrder"]) || undefined;

    return {
      status: statusParam ? (statusParam.split(",") as DocumentStatus[]) : undefined,
      dateFrom,
      dateTo,
      amountMin,
      amountMax,
      hospitalId,
      contractId,
      receiptId,
      search,
      sortBy,
      sortOrder,
    };
  });

  const updateFilters = (newFilters: Partial<DocumentFilters>) => {
    const updated = { ...filters, ...newFilters };
    setFilters(updated);

    const params = new URLSearchParams();
    if (updated.status && updated.status.length > 0) {
      params.set("status", updated.status.join(","));
    }
    if (updated.dateFrom) params.set("dateFrom", updated.dateFrom);
    if (updated.dateTo) params.set("dateTo", updated.dateTo);
    if (updated.amountMin !== undefined) params.set("amountMin", updated.amountMin.toString());
    if (updated.amountMax !== undefined) params.set("amountMax", updated.amountMax.toString());
    if (updated.hospitalId) params.set("hospitalId", updated.hospitalId);
    if (updated.contractId) params.set("contractId", updated.contractId);
    if (updated.receiptId) params.set("receiptId", updated.receiptId);
    if (updated.search) params.set("search", updated.search);
    if (updated.sortBy) params.set("sortBy", updated.sortBy);
    if (updated.sortOrder) params.set("sortOrder", updated.sortOrder);

    const queryString = params.toString();
    const newUrl = queryString ? `${location}?${queryString}` : location.split("?")[0];
    window.history.replaceState({}, "", newUrl);
  };

  const clearFilters = () => {
    setFilters({});
    window.history.replaceState({}, "", location.split("?")[0]);
  };

  const setDateRange = (range: "thisMonth" | "thisYear" | "custom", custom?: { from: Date; to: Date }) => {
    if (range === "thisMonth") {
      const { from, to } = getThisMonthRange();
      updateFilters({
        dateFrom: from.toISOString(),
        dateTo: to.toISOString(),
      });
    } else if (range === "thisYear") {
      const { from, to } = getThisYearRange();
      updateFilters({
        dateFrom: from.toISOString(),
        dateTo: to.toISOString(),
      });
    } else if (range === "custom" && custom) {
      updateFilters({
        dateFrom: custom.from.toISOString(),
        dateTo: custom.to.toISOString(),
      });
    }
  };

  return {
    filters,
    updateFilters,
    clearFilters,
    setDateRange,
  };
}



