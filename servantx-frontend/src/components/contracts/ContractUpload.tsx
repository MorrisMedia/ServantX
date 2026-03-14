import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { seedSyntheticContract, uploadContract, uploadContractsBulk } from "@/lib/api/contracts";
import { formatFileSize, validateFileSize, validateFileType } from "@/lib/utils/validation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Files, FileText, Upload, X } from "lucide-react";
import { DragEvent, useRef, useState } from "react";
import { toast } from "sonner";

const MAX_FILE_SIZE_MB = 500;
const ALLOWED_FILE_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/zip",
  "application/x-zip-compressed",
  ".pdf",
  ".doc",
  ".docx",
  ".zip",
];

export function ContractUpload() {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const singleUploadMutation = useMutation({
    mutationFn: uploadContract,
    onSuccess: (data) => {
      toast.success(data.message || "Contract uploaded. Processing continues in the background.");
      setFiles([]);
      queryClient.invalidateQueries({ queryKey: ["/contracts"] });
      queryClient.invalidateQueries({ queryKey: ["/rules"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to upload contract");
      setError(err.message || "Upload failed");
    },
  });

  const bulkUploadMutation = useMutation({
    mutationFn: uploadContractsBulk,
    onSuccess: (data) => {
      const successCount = data.contracts.length;
      const failCount = data.failedUploads.length;

      if (failCount === 0) {
        toast.success(`Uploaded ${successCount} contract(s). Processing continues in the background.`);
      } else {
        toast.warning(`Uploaded ${successCount} contract(s), ${failCount} failed`);
        data.failedUploads.forEach((fail) => {
          toast.error(`Failed: ${fail.fileName} - ${fail.error}`);
        });
      }

      setFiles([]);
      queryClient.invalidateQueries({ queryKey: ["/contracts"] });
      queryClient.invalidateQueries({ queryKey: ["/rules"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to upload contracts");
      setError(err.message || "Upload failed");
    },
  });

  const seedSyntheticMutation = useMutation({
    mutationFn: seedSyntheticContract,
    onSuccess: (data) => {
      toast.success(data.message || "Synthetic contract seeded. Processing continues in the background.");
      queryClient.invalidateQueries({ queryKey: ["/contracts"] });
      queryClient.invalidateQueries({ queryKey: ["/rules"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to seed synthetic contract");
      setError(err.message || "Failed to seed synthetic contract");
    },
  });

  const validateFile = (selectedFile: File): boolean => {
    if (!validateFileType(selectedFile, ALLOWED_FILE_TYPES)) {
      return false;
    }
    if (!validateFileSize(selectedFile, MAX_FILE_SIZE_MB)) {
      return false;
    }
    return true;
  };

  const handleFilesSelect = (selectedFiles: FileList | File[]) => {
    setError(null);
    const fileArray = Array.from(selectedFiles);
    const validFiles: File[] = [];
    const invalidFiles: string[] = [];

    fileArray.forEach((file) => {
      if (validateFile(file)) {
        validFiles.push(file);
      } else {
        invalidFiles.push(file.name);
      }
    });

    if (invalidFiles.length > 0) {
      setError(`Invalid files skipped: ${invalidFiles.join(", ")}. Only PDF, DOC, DOCX, ZIP under ${MAX_FILE_SIZE_MB}MB allowed.`);
    }

    if (validFiles.length > 0) {
      setFiles((prev) => [...prev, ...validFiles]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesSelect(e.target.files);
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
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelect(e.dataTransfer.files);
    }
  };

  const handleUpload = () => {
    if (files.length === 0) return;

    if (files.length === 1) {
      singleUploadMutation.mutate(files[0]);
    } else {
      bulkUploadMutation.mutate(files);
    }
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleClearAll = () => {
    setFiles([]);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const isUploading = singleUploadMutation.isPending || bulkUploadMutation.isPending;
  const isSuccess = singleUploadMutation.isSuccess || bulkUploadMutation.isSuccess;
  const isSeeding = seedSyntheticMutation.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Files className="h-5 w-5" />
          Upload Contracts
        </CardTitle>
        <CardDescription>
          Upload one or multiple contract files to extract rules. Supported formats: PDF, DOC, DOCX, ZIP (max {MAX_FILE_SIZE_MB}MB each)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
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
            accept=".pdf,.doc,.docx,.zip"
            multiple
            onChange={handleFileInputChange}
            className="hidden"
          />
          <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-sm font-medium mb-2">
            {isDragActive ? "Drop files here" : "Drag & drop contract files here"}
          </p>
          <p className="text-xs text-muted-foreground">or click to browse (multiple files supported)</p>
        </div>

        <div className="flex flex-col gap-3 rounded-lg border bg-muted/30 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium">Need sample data quickly?</p>
            <p className="text-xs text-muted-foreground">
              Seed a synthetic contract instantly to test dashboard flows.
            </p>
          </div>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setError(null);
              seedSyntheticMutation.mutate();
            }}
            disabled={isUploading || isSeeding}
          >
            {isSeeding ? "Seeding..." : "Seed Synthetic Contract"}
          </Button>
        </div>

        {files.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">{files.length} file(s) selected</p>
              <Button variant="ghost" size="sm" onClick={handleClearAll}>
                Clear all
              </Button>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-2">
              {files.map((file, index) => (
                <div key={`${file.name}-${index}`} className="flex items-center gap-4 p-3 border rounded-lg bg-muted/30">
                  <FileText className="h-6 w-6 text-primary shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => handleRemoveFile(index)}>
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
          <Button
            onClick={handleUpload}
            disabled={isUploading}
            className="w-full"
          >
            {isUploading ? (
              "Uploading..."
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload {files.length} Contract{files.length > 1 ? "s" : ""}
              </>
            )}
          </Button>
        )}

        {isSuccess && (
          <div className="flex items-center gap-2 text-sm text-green-600">
            <CheckCircle2 className="h-4 w-4" />
            Upload complete. Contract rules engine is running in the backend (safe to leave this page).
          </div>
        )}
      </CardContent>
    </Card>
  );
}

