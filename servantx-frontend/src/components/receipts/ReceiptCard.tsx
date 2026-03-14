import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { scanBillingRecordForIssues } from "@/lib/api/receipts";
import { BillingRecord } from "@/lib/types/receipt";
import { formatCurrency } from "@/lib/utils/currency";
import { formatRelativeTime } from "@/lib/utils/date";
import { formatFileSize } from "@/lib/utils/validation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, Clock, FileText, Link as LinkIcon, Scan } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Link } from "wouter";

interface BillingRecordCardProps {
  billingRecord: BillingRecord;
}

export function BillingRecordCard({ billingRecord }: BillingRecordCardProps) {
  const queryClient = useQueryClient();
  const [isScanning, setIsScanning] = useState(false);

  const scanMutation = useMutation({
    mutationFn: () => scanBillingRecordForIssues(billingRecord.id),
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ["/receipts"] });
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to scan billing record");
    },
    onSettled: () => {
      setIsScanning(false);
    },
  });

  const handleScan = () => {
    setIsScanning(true);
    scanMutation.mutate();
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">{billingRecord.fileName}</h3>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>{formatCurrency(billingRecord.amount)}</span>
              {billingRecord.fileSize && <span>• {formatFileSize(billingRecord.fileSize)}</span>}
              <span>• {formatRelativeTime(billingRecord.uploadedAt)}</span>
            </div>
            {billingRecord.hasDifference && (
              <div className="flex items-center gap-2">
                <Badge variant="default">Has Underpayment</Badge>
                {billingRecord.documentId && (
                  <Link href={`/dashboard/documents?receiptId=${billingRecord.id}`} className="flex items-center gap-1 text-sm text-primary hover:underline">
                    <LinkIcon className="h-3 w-3" />
                    View Docs
                  </Link>
                )}
              </div>
            )}
            {!billingRecord.documentId && (
              <Button
                onClick={handleScan}
                disabled={isScanning}
                size="sm"
                variant="outline"
                className="mt-2"
              >
                <Scan className="h-4 w-4 mr-2" />
                {isScanning ? "Scanning..." : "Scan for Issues"}
              </Button>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            {billingRecord.status === "processed" && (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            )}
            {billingRecord.status === "error" && (
              <AlertCircle className="h-5 w-5 text-red-500" />
            )}
            {billingRecord.status === "pending" && (
              <Clock className="h-5 w-5 text-yellow-500" />
            )}
            {billingRecord.status && (
              <span className="text-xs text-muted-foreground capitalize">{billingRecord.status}</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export const ReceiptCard = BillingRecordCard;



