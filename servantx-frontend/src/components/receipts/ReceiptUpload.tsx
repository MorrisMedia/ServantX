import { useState, useRef, DragEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadBillingRecord } from "@/lib/api/receipts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, FileText, X, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { validateFileSize, validateFileType, formatFileSize } from "@/lib/utils/validation";
import { Link } from "wouter";

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

export function BillingRecordUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: uploadBillingRecord,
    onSuccess: (data) => {
      toast.success("Billing record uploaded. Rules scan is running in the background.");
      setFile(null);
      queryClient.invalidateQueries({ queryKey: ["/receipts"] });
      if (data.document) {
        queryClient.invalidateQueries({ queryKey: ["/documents"] });
      }
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to upload billing record");
      setError(err.message || "Upload failed");
    },
  });

  const validateFile = (selectedFile: File): boolean => {
    setError(null);

    if (!validateFileType(selectedFile, ALLOWED_FILE_TYPES)) {
      setError("Invalid file type. Please upload PDF, JPG/PNG, CSV, EDI, HL7/HLZ, DAT, JSON, ZIP, TXT, 835, or 837 files.");
      return false;
    }

    if (!validateFileSize(selectedFile, MAX_FILE_SIZE_MB)) {
      setError(`File size exceeds ${MAX_FILE_SIZE_MB}MB limit.`);
      return false;
    }

    return true;
  };

  const handleFileSelect = (selectedFile: File) => {
    if (validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
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
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleUpload = () => {
    if (!file) return;
    uploadMutation.mutate(file);
  };

  const handleRemove = () => {
    setFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Billing Record</CardTitle>
        <CardDescription>
          Upload a single billing record or ZIP file. Supported formats: PDF, JPG/PNG, CSV, EDI, HL7/HLZ, DAT, JSON, ZIP, TXT, 835, 837 (max {MAX_FILE_SIZE_MB}MB). Rule scan starts automatically.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!file ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-primary/50"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.csv,.edi,.hl7,.hlz,.dat,.json,.zip,.txt,.835,.837"
              onChange={handleFileInputChange}
              className="hidden"
            />
            <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-sm font-medium mb-2">
              {isDragActive ? "Drop the file here" : "Drag & drop a billing record file here"}
            </p>
            <p className="text-xs text-muted-foreground">or click to browse</p>
          </div>
        ) : (
          <div className="flex items-center gap-4 p-4 border rounded-lg">
            <FileText className="h-8 w-8 text-primary" />
            <div className="flex-1">
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={handleRemove}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {file && (
          <Button
            onClick={handleUpload}
            disabled={uploadMutation.isPending}
            className="w-full"
          >
            {uploadMutation.isPending ? (
              "Uploading..."
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload Billing Record
              </>
            )}
          </Button>
        )}

        {uploadMutation.isSuccess && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              Billing record uploaded. Rules scan is running.
            </div>
            {uploadMutation.data.document && (
              <div className="text-sm text-muted-foreground">
                A document has been generated.{" "}
                <Link href="/dashboard/documents" className="text-primary hover:underline">
                  View document
                </Link>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export const ReceiptUpload = BillingRecordUpload;



