import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  deleteBillingRecord,
  getBillingRecords,
  scanBillingRecordForIssues,
  uploadBillingRecord,
  uploadBillingRecordsBulk,
} from "@/lib/api/receipts";
import { formatCurrency } from "@/lib/utils/currency";
import { formatDate } from "@/lib/utils/date";
import { formatFileSize, validateFileSize, validateFileType } from "@/lib/utils/validation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, FileText, Info, Scan, Search, Trash2, Upload, X } from "lucide-react";
import { DragEvent, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Link } from "wouter";

const LIMIT = 15;
const MAX_FILE_SIZE_MB = 50;
const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "image/jpg",
  "text/csv",
  "application/csv",
  "application/vnd.ms-excel",
  "application/json",
  "application/fhir+json",
  "text/plain",
  "application/octet-stream",
  "text/x-edi",
  "application/edi-x12",
  "text/x-hl7",
  "application/hl7-v2",
  "text/hl7",
  "text/x-hlz",
  "application/hlz",
  "text/hlz",
];
const ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".csv", ".edi", ".hl7", ".hlz", ".dat", ".json"];
const ALLOWED_FILE_TYPES = [...ALLOWED_MIME_TYPES, ...ALLOWED_EXTENSIONS];

export default function BillingRecordsPage() {
  const queryClient = useQueryClient();
  const [scanningIds, setScanningIds] = useState<Set<string>>(new Set());
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [violationFilter, setViolationFilter] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(0);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const [isDropActive, setIsDropActive] = useState(false);
  const [dropError, setDropError] = useState<string | null>(null);
  const [lastDroppedFiles, setLastDroppedFiles] = useState<File[]>([]);
  const dropInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["receipts", { search: searchQuery, status: statusFilter, violation: violationFilter, page }],
    queryFn: () => getBillingRecords({
      search: searchQuery || undefined,
      status: statusFilter !== "all" ? [statusFilter] : undefined,
      hasDifference: violationFilter === "yes" ? true : violationFilter === "no" ? false : undefined,
      limit: LIMIT,
      offset: page * LIMIT,
    }),
    refetchInterval: (query) => {
      const result = query.state.data as
        | { items?: Array<{ status?: string }> }
        | Array<{ status?: string }>
        | undefined;
      const records = Array.isArray(result) ? result : result?.items || [];
      return records.some((record) => record.status === "processing") ? 2000 : false;
    },
  });

  const billingRecords = Array.isArray(data) ? data : (data?.items || []);
  const total = Array.isArray(data) ? data.length : (data?.total || 0);
  const hasMore = Array.isArray(data) ? false : (data?.hasMore || false);
  const totalPages = Math.ceil(total / LIMIT);

  const scanMutation = useMutation({
    mutationFn: (billingRecordId: string) => scanBillingRecordForIssues(billingRecordId),
    onSuccess: (data, billingRecordId) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ["receipts"] });
      setScanningIds((prev) => {
        const next = new Set(prev);
        next.delete(billingRecordId);
        return next;
      });
    },
    onError: (error: Error, billingRecordId) => {
      toast.error(error.message || "Failed to scan billing record");
      setScanningIds((prev) => {
        const next = new Set(prev);
        next.delete(billingRecordId);
        return next;
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (billingRecordIds: string[]) => {
      await Promise.all(billingRecordIds.map((id) => deleteBillingRecord(id)));
      return billingRecordIds;
    },
    onSuccess: (billingRecordIds) => {
      toast.success(
        billingRecordIds.length > 1
          ? `Deleted ${billingRecordIds.length} billing records`
          : "Billing record deleted",
      );
      queryClient.invalidateQueries({ queryKey: ["receipts"] });
      queryClient.invalidateQueries({ queryKey: ["/receipts"] });
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
      setDeletingIds((prev) => {
        const next = new Set(prev);
        billingRecordIds.forEach((id) => next.delete(id));
        return next;
      });
      setSelectedIds((prev) => {
        const next = new Set(prev);
        billingRecordIds.forEach((id) => next.delete(id));
        return next;
      });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to delete billing record");
      setDeletingIds(new Set());
    },
  });

  const quickDropUploadMutation = useMutation({
    mutationFn: async (files: File[]) => {
      if (files.length === 1) {
        await uploadBillingRecord(files[0]);
        return files.length;
      }
      await uploadBillingRecordsBulk(files);
      return files.length;
    },
    onSuccess: (count) => {
      toast.success(`Uploaded ${count} billing record${count > 1 ? "s" : ""}. Rules scan is running in the background.`);
      setDropError(null);
      queryClient.invalidateQueries({ queryKey: ["receipts"] });
      queryClient.invalidateQueries({ queryKey: ["/receipts"] });
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
    },
    onError: (err: Error) => {
      const message = err.message || "Failed to upload billing records";
      setDropError(message);
      toast.error(message);
    },
  });

  const handleScan = (billingRecordId: string) => {
    setScanningIds((prev) => new Set(prev).add(billingRecordId));
    scanMutation.mutate(billingRecordId);
  };

  const isScanning = (billingRecordId: string) => scanningIds.has(billingRecordId);
  const isDeleting = (billingRecordId: string) => deletingIds.has(billingRecordId);
  const deletableRecords = billingRecords.filter((record) => record.status !== "processing");
  const selectedDeletableCount = deletableRecords.filter((record) => selectedIds.has(record.id)).length;
  const allDeletableSelected =
    deletableRecords.length > 0 && selectedDeletableCount === deletableRecords.length;

  useEffect(() => {
    setSelectedIds((prev) => {
      const visibleIds = new Set(billingRecords.map((record) => record.id));
      return new Set(Array.from(prev).filter((id) => visibleIds.has(id)));
    });
  }, [billingRecords]);

  const handleToggleAll = (checked: boolean) => {
    if (!checked) {
      setSelectedIds(new Set());
      return;
    }
    setSelectedIds(new Set(deletableRecords.map((record) => record.id)));
  };

  const handleToggleSelected = (billingRecordId: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(billingRecordId);
      else next.delete(billingRecordId);
      return next;
    });
  };

  const handleDelete = (billingRecordId: string, fileName: string) => {
    const confirmed = window.confirm(`Delete billing record "${fileName}"? This cannot be undone.`);
    if (!confirmed) return;
    setDeletingIds((prev) => new Set(prev).add(billingRecordId));
    deleteMutation.mutate([billingRecordId]);
  };

  const handleDeleteSelected = () => {
    const ids = billingRecords
      .filter((record) => selectedIds.has(record.id) && record.status !== "processing")
      .map((record) => record.id);
    if (ids.length === 0) return;

    const confirmed = window.confirm(`Delete ${ids.length} selected billing records? This cannot be undone.`);
    if (!confirmed) return;

    setDeletingIds((prev) => new Set([...Array.from(prev), ...ids]));
    deleteMutation.mutate(ids);
  };

  const handleSearch = () => {
    setSearchQuery(searchInput);
    setPage(0);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const clearFilters = () => {
    setSearchInput("");
    setSearchQuery("");
    setStatusFilter("all");
    setViolationFilter(undefined);
    setPage(0);
  };

  const hasActiveFilters = searchQuery !== "" || statusFilter !== "all" || violationFilter !== undefined;

  const validateDroppedFiles = (files: File[]): File[] => {
    const valid: File[] = [];
    const invalidMessages: string[] = [];

    files.forEach((file) => {
      if (!validateFileType(file, ALLOWED_FILE_TYPES)) {
        invalidMessages.push(`${file.name}: invalid type`);
        return;
      }
      if (!validateFileSize(file, MAX_FILE_SIZE_MB)) {
        invalidMessages.push(`${file.name}: exceeds ${MAX_FILE_SIZE_MB}MB`);
        return;
      }
      valid.push(file);
    });

    if (invalidMessages.length > 0) {
      setDropError(
        `Some files were skipped: ${invalidMessages.join(", ")}. Allowed formats: PDF, JPG/PNG, CSV, EDI, HL7/HLZ, DAT, JSON.`,
      );
    } else {
      setDropError(null);
    }

    return valid;
  };

  const startQuickDropUpload = (files: File[]) => {
    const validFiles = validateDroppedFiles(files);
    if (validFiles.length === 0) return;
    setLastDroppedFiles(validFiles);
    quickDropUploadMutation.mutate(validFiles);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDropActive(false);
    const droppedFiles = Array.from(e.dataTransfer.files || []);
    if (droppedFiles.length > 0) {
      startQuickDropUpload(droppedFiles);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Billing Records</h1>
            <p className="text-muted-foreground">
              View and manage all uploaded billing records
            </p>
          </div>
          <Button asChild>
            <Link href="/dashboard/billing-records/upload">
              <Upload className="mr-2 h-4 w-4" />
              Upload Billing Records
            </Link>
          </Button>
        </div>

        <div className="rounded-lg border border-blue-500 bg-blue-500/10 p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-600 mb-1">How Billing Records Work</h3>
              <p className="text-sm text-blue-600/80">
                Upload your billing records and they will be scanned against your contracts. If a billing record violates any contract rules, a document is automatically created highlighting the discrepancies for review.
              </p>
            </div>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Quick Drop Upload</CardTitle>
            <CardDescription>
              Drag and drop one or more billing records here (PDF/JPG/PNG, CSV, EDI, HL7/HLZ, DAT, JSON; max {MAX_FILE_SIZE_MB}MB each). Rule scan starts automatically.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDropActive(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setIsDropActive(false);
              }}
              onDrop={handleDrop}
              onClick={() => dropInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDropActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
              }`}
            >
              <input
                ref={dropInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.csv,.edi,.hl7,.hlz,.dat,.json"
                multiple
                className="hidden"
                onChange={(e) => {
                  const selected = Array.from(e.target.files || []);
                  if (selected.length > 0) {
                    startQuickDropUpload(selected);
                  }
                }}
              />
              <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
              <p className="text-sm font-medium">
                {isDropActive ? "Drop files to upload" : "Drag and drop billing records here"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">or click to browse files</p>
            </div>

            {quickDropUploadMutation.isPending && lastDroppedFiles.length > 0 && (
              <div className="rounded-md bg-muted/50 p-3 text-sm">
                Uploading {lastDroppedFiles.length} file{lastDroppedFiles.length > 1 ? "s" : ""}...
              </div>
            )}

            {dropError && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {dropError}
              </div>
            )}

            {!quickDropUploadMutation.isPending && lastDroppedFiles.length > 0 && !dropError && (
              <div className="rounded-md bg-green-500/10 p-3 text-sm text-green-700">
                Last upload: {lastDroppedFiles.length} file{lastDroppedFiles.length > 1 ? "s" : ""} (
                {lastDroppedFiles.map((file) => formatFileSize(file.size)).join(", ")}).
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>Billing Records</CardTitle>
                <CardDescription>
                  {total > 0 ? `Showing ${page * LIMIT + 1}-${Math.min((page + 1) * LIMIT, total)} of ${total} billing records` : "All uploaded billing records"}
                </CardDescription>
              </div>
            </div>

            <div className="flex flex-col gap-3 pt-4 sm:flex-row sm:items-center">
              <div className="relative flex-1 flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search by file name..."
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="pl-9"
                  />
                </div>
                <Button onClick={handleSearch} variant="secondary">
                  <Search className="h-4 w-4" />
                </Button>
              </div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(0);
                }}
                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm w-full sm:w-[150px]"
                aria-label="Filter by status"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="processing">Processing</option>
                <option value="processed">Processed</option>
                <option value="error">Error</option>
              </select>
              <select
                value={violationFilter || "all"}
                onChange={(e) => {
                  const v = e.target.value;
                  setViolationFilter(v === "all" ? undefined : v);
                  setPage(0);
                }}
                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm w-full sm:w-[150px]"
                aria-label="Filter by violations"
              >
                <option value="all">All</option>
                <option value="yes">Has Violations</option>
                <option value="no">No Violations</option>
              </select>
              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  <X className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              )}
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDeleteSelected}
                disabled={selectedDeletableCount === 0 || deleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                {deleteMutation.isPending
                  ? "Deleting..."
                  : `Delete Selected${selectedDeletableCount > 0 ? ` (${selectedDeletableCount})` : ""}`}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : error ? (
              <div className="text-center text-destructive py-8">
                Failed to load billing records. Please try again.
              </div>
            ) : billingRecords.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>{hasActiveFilters ? "No billing records match your filters" : "No billing records found"}</p>
                {hasActiveFilters ? (
                  <Button variant="outline" className="mt-4" onClick={clearFilters}>
                    Clear Filters
                  </Button>
                ) : (
                  <Button asChild variant="outline" className="mt-4">
                    <Link href="/dashboard/billing-records/upload">
                      <Upload className="mr-2 h-4 w-4" />
                      Upload Your First Billing Record
                    </Link>
                  </Button>
                )}
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[40px]">
                        <input
                          type="checkbox"
                          checked={allDeletableSelected}
                          onChange={(e) => handleToggleAll(e.target.checked)}
                          aria-label="Select all billing records"
                          disabled={deletableRecords.length === 0}
                          className="h-4 w-4 rounded border border-input accent-primary disabled:cursor-not-allowed disabled:opacity-50"
                        />
                      </TableHead>
                      <TableHead>File Name</TableHead>
                      <TableHead>Underpayment</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Violation</TableHead>
                      <TableHead>File Size</TableHead>
                      <TableHead>Uploaded</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {billingRecords.map((billingRecord) => (
                      <TableRow key={billingRecord.id}>
                        <TableCell>
                          <input
                            type="checkbox"
                            checked={selectedIds.has(billingRecord.id)}
                            onChange={(e) => handleToggleSelected(billingRecord.id, e.target.checked)}
                            aria-label={`Select ${billingRecord.fileName}`}
                            disabled={billingRecord.status === "processing" || isDeleting(billingRecord.id)}
                            className="h-4 w-4 rounded border border-input accent-primary disabled:cursor-not-allowed disabled:opacity-50"
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            {billingRecord.fileName}
                          </div>
                        </TableCell>
                        <TableCell>
                          {billingRecord.amount > 0 ? (
                            <span className="text-destructive font-medium">
                              {formatCurrency(billingRecord.amount)}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant={billingRecord.status === "processed" ? "default" : "secondary"}>
                            {billingRecord.status || "pending"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={billingRecord.hasDifference ? "destructive" : "outline"}>
                            {billingRecord.hasDifference ? "Yes" : "No"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {billingRecord.fileSize ? formatFileSize(billingRecord.fileSize) : "-"}
                        </TableCell>
                        <TableCell>{formatDate(billingRecord.uploadedAt)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleScan(billingRecord.id)}
                              disabled={isScanning(billingRecord.id) || billingRecord.status === "processing" || isDeleting(billingRecord.id)}
                            >
                              <Scan className="h-4 w-4 mr-1" />
                              {isScanning(billingRecord.id)
                                ? "Scanning..."
                                : billingRecord.status === "processing"
                                  ? "Running..."
                                  : "Scan"}
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDelete(billingRecord.id, billingRecord.fileName)}
                              disabled={isDeleting(billingRecord.id) || billingRecord.status === "processing"}
                            >
                              <Trash2 className="h-4 w-4 mr-1" />
                              {isDeleting(billingRecord.id) ? "Deleting..." : "Delete"}
                            </Button>
                            {billingRecord.hasDifference && (
                              <Button asChild size="sm" variant="link">
                                <Link href={`/dashboard/documents?search=${encodeURIComponent(billingRecord.fileName)}`}>
                                  View Docs
                                </Link>
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {totalPages > 1 && (
                  <div className="flex items-center justify-between pt-4 border-t mt-4">
                    <p className="text-sm text-muted-foreground">
                      Page {page + 1} of {totalPages}
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(0, p - 1))}
                        disabled={page === 0}
                      >
                        <ChevronLeft className="h-4 w-4 mr-1" />
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => p + 1)}
                        disabled={!hasMore}
                      >
                        Next
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
