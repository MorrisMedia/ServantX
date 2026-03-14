import { useQuery } from "@tanstack/react-query";
import { getBillingRecords } from "@/lib/api/receipts";
import { BillingRecordCard } from "./ReceiptCard";
import { BillingRecordFilters } from "@/lib/types/receipt";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { FileText } from "lucide-react";

interface BillingRecordListProps {
  filters?: BillingRecordFilters;
}

export function BillingRecordList({ filters }: BillingRecordListProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["/receipts", filters],
    queryFn: () => getBillingRecords(filters),
  });

  const billingRecords = Array.isArray(data) ? data : (data?.items || []);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-6 w-1/3 mb-2" />
              <Skeleton className="h-4 w-1/2" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-destructive">
            Failed to load billing records. Please try again.
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!billingRecords || billingRecords.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No billing records found</h3>
          <p className="text-sm text-muted-foreground">
            Upload your first billing record to get started.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {billingRecords.map((billingRecord) => (
        <BillingRecordCard key={billingRecord.id} billingRecord={billingRecord} />
      ))}
    </div>
  );
}

export const ReceiptList = BillingRecordList;



