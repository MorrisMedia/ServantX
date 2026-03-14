import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { uploadBillingRecordsBulk } from "@/lib/api/receipts";
import { formatFileSize, validateFileSize, validateFileType } from "@/lib/utils/validation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FileText, Loader2, Upload, X } from "lucide-react";
import { DragEvent, useRef, useState } from "react";
import { toast } from "sonner";
import { useLocation } from "wouter";

const MAX_FILE_SIZE_MB = 500;
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
  "application/zip",
  "application/x-zip-compressed",
];
const ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".csv", ".edi", ".hl7", ".hlz", ".dat", ".json", ".zip", ".txt", ".835", ".837"];
const ALLOWED_FILE_TYPES = [...ALLOWED_MIME_TYPES, ...ALLOWED_EXTENSIONS];

export function BillingRecordBulkUpload() {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [, setLocation] = useLocation();

  const uploadMutation = useMutation({
    mutationFn: uploadBillingRecordsBulk,
    onSuccess: () => {
      toast.success(`${files.length} billing record(s) uploaded. Rules scan is running in the background.`);
      setFiles([]);
      queryClient.invalidateQueries({ queryKey: ["receipts"] });
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
      setLocation("/dashboard/billing-records");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to upload billing records");
      setError(err.message || "Upload failed");
    },
  });

  const validateFiles = (selectedFiles: File[]): File[] => {
    setError(null);
    const validFiles: File[] = [];

    selectedFiles.forEach((file) => {
      if (!validateFileType(file, ALLOWED_FILE_TYPES)) {
        setError(`Invalid file type: ${file.name}. Please upload PDF, JPG/PNG, CSV, EDI, HL7/HLZ, DAT, JSON, ZIP, TXT, 835, or 837 files.`);
        return;
      }

      if (!validateFileSize(file, MAX_FILE_SIZE_MB)) {
        setError(`File size exceeds ${MAX_FILE_SIZE_MB}MB limit: ${file.name}`);
        return;
      }

      validFiles.push(file);
    });

    return validFiles;
  };

  const handleFilesSelect = (selectedFiles: File[]) => {
    const validFiles = validateFiles(selectedFiles);
    if (validFiles.length > 0) {
      setFiles((prev) => [...prev, ...validFiles]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length > 0) {
      handleFilesSelect(selectedFiles);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragActive(false);
    const droppedFiles = Array.from(e.dataTransfer.files || []);
    if (droppedFiles.length > 0) {
      handleFilesSelect(droppedFiles);
    }
  };

  const handleUpload = () => {
    if (files.length === 0) return;
    uploadMutation.mutate(files);
  };

  const handleRemove = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setError(null);
  };

  const handleClearAll = () => {
    setFiles([]);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Billing Records</CardTitle>
        <CardDescription>
          Upload one or more billing record files (including ZIP). Supported formats: PDF, JPG/PNG, CSV, EDI, HL7/HLZ, DAT, JSON, ZIP, TXT, 835, 837 (max {MAX_FILE_SIZE_MB}MB per file). Rule scan starts automatically.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {files.length === 0 ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-primary/50"
              }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.csv,.edi,.hl7,.hlz,.dat,.json,.zip,.txt,.835,.837"
              multiple
              onChange={handleFileInputChange}
              className="hidden"
            />
            <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-sm font-medium mb-2">
              {isDragActive ? "Drop files here" : "Drag & drop billing record files here"}
            </p>
            <p className="text-xs text-muted-foreground">or click to browse (multiple files)</p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">{files.length} file(s) selected</span>
              <Button variant="ghost" size="sm" onClick={handleClearAll}>
                Clear All
              </Button>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {files.map((file, index) => (
                <div key={index} className="flex items-center gap-4 p-3 border rounded-lg">
                  <FileText className="h-6 w-6 text-primary flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemove(index)}
                    className="flex-shrink-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {files.length > 0 && (
          <>
            <Button
              onClick={handleUpload}
              disabled={uploadMutation.isPending}
              className="w-full"
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading {files.length} file(s)...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload {files.length} Billing Record(s)
                </>
              )}
            </Button>
            {uploadMutation.isPending && (
              <Progress value={uploadMutation.isPending ? 50 : 100} className="w-full" />
            )}
          </>
        )}

      </CardContent>
    </Card>
  );
}

export const ReceiptBulkUpload = BillingRecordBulkUpload;



