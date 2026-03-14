import { useQuery } from "@tanstack/react-query";
import { getInvoices } from "@/lib/api/invoices";
import { InvoiceFilters } from "@/lib/types/invoice";
import { Card, CardContent } from "@/components/ui/card";
import { formatDate } from "@/lib/utils/date";
import { formatCurrency } from "@/lib/utils/currency";
import { Skeleton } from "@/components/ui/skeleton";
import { Receipt as ReceiptIcon } from "lucide-react";

interface InvoiceListProps {
  filters?: InvoiceFilters;
}

export function InvoiceList({ filters }: InvoiceListProps) {
  const { data: invoices, isLoading, error } = useQuery({
    queryKey: ["/invoices", filters],
    queryFn: () => getInvoices(filters),
  });

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
            Failed to load invoices. Please try again.
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!invoices || invoices.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <ReceiptIcon className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No invoices found</h3>
          <p className="text-sm text-muted-foreground">
            Invoices will appear here when available.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {invoices.map((invoice) => (
        <Card key={invoice.id} className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <ReceiptIcon className="h-5 w-5 text-primary" />
                  <h3 className="font-semibold">
                    {invoice.invoiceNumber || `Invoice #${invoice.id.slice(0, 8)}`}
                  </h3>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>{formatCurrency(invoice.amount)}</span>
                  <span>• {formatDate(invoice.date)}</span>
                  {invoice.payer && <span>• {invoice.payer}</span>}
                </div>
              </div>
              {invoice.status && (
                <span className="text-xs text-muted-foreground capitalize">{invoice.status}</span>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

