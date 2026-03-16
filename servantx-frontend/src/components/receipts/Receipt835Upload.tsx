import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { upload835Batch } from "@/lib/api/batches";
import { formatFileSize, validateFileSize } from "@/lib/utils/validation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Archive, Loader2, Upload, X } from "lucide-react";
import { DragEvent, useRef, useState } from "react";
import type { AuditPayerScope } from "@/lib/types/audit";
import { toast } from "sonner";
import { useLocation } from "wouter";

const MAX_FILE_SIZE_MB = 500;

interface BillingRecord835UploadProps {
  onBatchQueued?: (batchId: string) => void;
}

export function BillingRecord835Upload({ onBatchQueued }: BillingRecord835UploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [payerScope, setPayerScope] = useState<AuditPayerScope>("CONTRACT_AUDIT");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [, setLocation] = useLocation();

  const uploadMutation = useMutation({
    mutationFn: upload835Batch,
    onSuccess: (data) => {
      toast.success(data.message || "835 batch queued");
      setFiles([]);
      queryClient.invalidateQueries({ queryKey: ["/analysis"] });
      queryClient.invalidateQueries({ queryKey: ["/analysis/patterns"] });
      queryClient.invalidateQueries({ queryKey: ["/batches"] });
      if (data.batch?.id) {
        onBatchQueued?.(data.batch.id);
        setLocation(`/dashboard/audit-workflow?batchId=${data.batch.id}`);
      }
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to queue 835 batch");
      setError(err.message || "Upload failed");
    },
  });

  const validateFile = (file: File): boolean => {
    const name = file.name.toLowerCase();
    const validExt = name.endsWith(".835") || name.endsWith(".edi") || name.endsWith(".txt");
    if (!validExt) {
      setError(`Invalid file extension for ${file.name}. Use .835, .edi, or .txt.`);
      return false;
    }
    if (!validateFileSize(file, MAX_FILE_SIZE_MB)) {
      setError(`${file.name} exceeds ${MAX_FILE_SIZE_MB}MB.`);
      return false;
    }
    return true;
  };

  const handleFilesSelect = (selectedFiles: File[]) => {
    setError(null);
    const valid = selectedFiles.filter(validateFile);
    if (valid.length > 0) setFiles((prev) => [...prev, ...valid]);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragActive(false);
    handleFilesSelect(Array.from(e.dataTransfer.files || []));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload 835 ERA Batch</CardTitle>
        <CardDescription>
          Upload one or more 835 remittance files for claim-level underpayment detection.
          Supported: .835, .edi, .txt (max {MAX_FILE_SIZE_MB}MB each).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {files.length === 0 ? (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragActive(true);
            }}
            onDragLeave={(e) => {
              e.preventDefault();
              setIsDragActive(false);
            }}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".835,.edi,.txt"
              multiple
              className="hidden"
              onChange={(e) => handleFilesSelect(Array.from(e.target.files || []))}
            />
            <Archive className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-sm font-medium mb-1">{isDragActive ? "Drop files here" : "Drag and drop 835 files here"}</p>
            <p className="text-xs text-muted-foreground">or click to browse</p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{files.length} file(s) selected</span>
              <Button variant="ghost" size="sm" onClick={() => setFiles([])}>
                Clear All
              </Button>
            </div>
            <div className="max-h-64 overflow-y-auto space-y-2">
              {files.map((file, index) => (
                <div key={`${file.name}-${index}`} className="flex items-center gap-3 p-3 border rounded-lg">
                  <Archive className="h-5 w-5 text-primary" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => setFiles((prev) => prev.filter((_, i) => i !== index))}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

        <div className="space-y-2 rounded-lg border p-4">
          <div className="text-sm font-medium">Pricing benchmark for this 835 batch</div>
          <div className="grid gap-2 md:grid-cols-3">
            <button type="button" className={`rounded border px-3 py-2 text-sm text-left ${payerScope === "CONTRACT_AUDIT" ? "border-primary bg-primary/5" : "border-border"}`} onClick={() => setPayerScope("CONTRACT_AUDIT")}>
              <div className="font-medium">Negotiated contracts</div>
              <div className="text-xs text-muted-foreground">Default. Use the hospital's uploaded contracts / rule libraries.</div>
            </button>
            <button type="button" className={`rounded border px-3 py-2 text-sm text-left ${payerScope === "MEDICARE" ? "border-primary bg-primary/5" : "border-border"}`} onClick={() => setPayerScope("MEDICARE")}>
              <div className="font-medium">Medicare</div>
              <div className="text-xs text-muted-foreground">Force CMS public-rate repricing for this batch.</div>
            </button>
            <button type="button" className={`rounded border px-3 py-2 text-sm text-left ${payerScope === "TX_MEDICAID_FFS" ? "border-primary bg-primary/5" : "border-border"}`} onClick={() => setPayerScope("TX_MEDICAID_FFS")}>
              <div className="font-medium">Texas Medicaid</div>
              <div className="text-xs text-muted-foreground">Force TX Medicaid FFS fee-schedule repricing for this batch.</div>
            </button>
          </div>
        </div>

        {files.length > 0 && (
          <Button className="w-full" onClick={() => uploadMutation.mutate({ files, payerScope })} disabled={uploadMutation.isPending}>
            {uploadMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Queueing batch...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Queue 835 Batch
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
