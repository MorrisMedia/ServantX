import { useState, useRef, DragEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadBillingRecordsZip } from "@/lib/api/receipts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, FileText, X, CheckCircle2, Loader2, Archive } from "lucide-react";
import { toast } from "sonner";
import { validateFileSize, formatFileSize } from "@/lib/utils/validation";

const MAX_FILE_SIZE_MB = 1024; // 1 GB limit for zip files

export function BillingRecordZipUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: uploadBillingRecordsZip,
    onSuccess: (data) => {
      toast.success(`Zip file processed successfully. ${data.billingRecords?.length || 0} billing records uploaded.`);
      setFile(null);
      queryClient.invalidateQueries({ queryKey: ["/receipts"] });
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to upload zip file");
      setError(err.message || "Upload failed");
    },
  });

  const validateFile = (selectedFile: File): boolean => {
    setError(null);

    // Check if it's a zip file
    const isZip = selectedFile.type === "application/zip" || 
                  selectedFile.type === "application/x-zip-compressed" ||
                  selectedFile.name.toLowerCase().endsWith(".zip");
    
    if (!isZip) {
      setError("Invalid file type. Please upload a ZIP file.");
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
        <CardTitle>Upload Billing Records from ZIP</CardTitle>
        <CardDescription>
          Upload a ZIP file containing multiple billing record files. Supported formats inside ZIP: PDF, JPG/PNG, CSV, EDI, HL7/HLZ, DAT, JSON (max {MAX_FILE_SIZE_MB}MB for ZIP file). Rule scan starts automatically.
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
              accept=".zip"
              onChange={handleFileInputChange}
              className="hidden"
            />
            <Archive className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-sm font-medium mb-2">
              {isDragActive ? "Drop the ZIP file here" : "Drag & drop a ZIP file here"}
            </p>
            <p className="text-xs text-muted-foreground">or click to browse</p>
          </div>
        ) : (
          <div className="flex items-center gap-4 p-4 border rounded-lg">
            <Archive className="h-8 w-8 text-primary" />
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
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing ZIP file...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload ZIP File
              </>
            )}
          </Button>
        )}

        {uploadMutation.isSuccess && (
          <div className="space-y-2">
            {uploadMutation.data.billingRecords && uploadMutation.data.billingRecords.length > 0 ? (
              <>
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle2 className="h-4 w-4" />
                  {uploadMutation.data.message || "ZIP file processed successfully"}
                </div>
                <div className="text-sm text-muted-foreground">
                  {uploadMutation.data.billingRecords.length} billing record(s) extracted and uploaded.
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2 text-sm text-yellow-600">
                <CheckCircle2 className="h-4 w-4" />
                ZIP file processed, but no valid billing record files found.
              </div>
            )}
            {uploadMutation.data.errors && uploadMutation.data.errors.length > 0 && (
              <div className="rounded-md bg-yellow-50 dark:bg-yellow-950 p-3 text-sm">
                <p className="font-medium text-yellow-800 dark:text-yellow-200 mb-1">
                  {uploadMutation.data.billingRecords && uploadMutation.data.billingRecords.length > 0 
                    ? "Some files were skipped:" 
                    : "Files in ZIP were not valid billing record files:"}
                </p>
                <ul className="list-disc list-inside space-y-1 text-yellow-700 dark:text-yellow-300 max-h-32 overflow-y-auto">
                  {uploadMutation.data.errors.map((error, index) => (
                    <li key={index} className="text-xs">{error}</li>
                  ))}
                </ul>
                <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-2">
                  Supported billing record files: PDF, JPG/PNG, CSV, EDI, HL7/HLZ, DAT, JSON.
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export const ReceiptZipUpload = BillingRecordZipUpload;

