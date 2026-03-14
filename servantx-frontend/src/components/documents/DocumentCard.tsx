import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Card, CardContent } from "@/components/ui/card";
import { Document } from "@/lib/types/document";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/utils/currency";
import { formatRelativeTime } from "@/lib/utils/date";
import { AlertCircle, ArrowRight, Calendar, CheckCircle2, Clock, DollarSign, FileText, XCircle } from "lucide-react";
import { Link } from "wouter";

interface DocumentCardProps {
  document: Document;
}

const defaultConfig = {
  icon: AlertCircle,
  color: "text-gray-600 dark:text-gray-400",
  bgColor: "bg-gray-50 dark:bg-gray-950/20",
  borderColor: "border-gray-200 dark:border-gray-800",
};

const statusConfig: Record<string, typeof defaultConfig> = {
  succeeded: {
    icon: CheckCircle2,
    color: "text-green-600 dark:text-green-400",
    bgColor: "bg-green-50 dark:bg-green-950/20",
    borderColor: "border-green-200 dark:border-green-800",
  },
  in_progress: {
    icon: Clock,
    color: "text-yellow-600 dark:text-yellow-400",
    bgColor: "bg-yellow-50 dark:bg-yellow-950/20",
    borderColor: "border-yellow-200 dark:border-yellow-800",
  },
  failed: {
    icon: XCircle,
    color: "text-red-600 dark:text-red-400",
    bgColor: "bg-red-50 dark:bg-red-950/20",
    borderColor: "border-red-200 dark:border-red-800",
  },
  not_submitted: defaultConfig,
};

export function DocumentCard({ document }: DocumentCardProps) {
  const config = statusConfig[document.status] || defaultConfig;
  const StatusIcon = config.icon;

  const hasUnderpayment = document.hasUnderpayment || (document.underpaymentAmount !== undefined && document.underpaymentAmount > 0);

  return (
    <Card className={cn(
      "group hover:shadow-lg transition-all duration-200 cursor-pointer border-l-4",
      hasUnderpayment ? "border-red-400 dark:border-red-600" : config.borderColor,
      "hover:scale-[1.01]"
    )}>
      <Link href={`/dashboard/documents/${document.id}`} className="block">
        <CardContent className="p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "p-2 rounded-lg",
                    hasUnderpayment ? "bg-red-50 dark:bg-red-950/20" : config.bgColor
                  )}>
                    <StatusIcon className={cn("h-5 w-5", hasUnderpayment ? "text-red-600 dark:text-red-400" : config.color)} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">
                      {document.name || `Document ${document.id.slice(0, 8)}`}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Billing Record: {document.receiptId ? `${document.receiptId.slice(0, 8)}...` : "Not linked"}
                    </p>
                  </div>
                </div>
                <StatusBadge status={document.status} />
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                {hasUnderpayment && document.receiptAmount !== undefined && (
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-md bg-gray-100 dark:bg-gray-800">
                      <DollarSign className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Paid</p>
                      <p className="font-semibold text-lg">{formatCurrency(document.receiptAmount)}</p>
                    </div>
                  </div>
                )}

                {hasUnderpayment && document.contractAmount !== undefined && (
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-md bg-blue-100 dark:bg-blue-900/30">
                      <DollarSign className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Should Pay</p>
                      <p className="font-semibold text-lg">{formatCurrency(document.contractAmount)}</p>
                    </div>
                  </div>
                )}

                {hasUnderpayment && document.underpaymentAmount !== undefined && (
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-md bg-red-100 dark:bg-red-900/30">
                      <DollarSign className="h-4 w-4 text-red-600 dark:text-red-400" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Underpayment</p>
                      <p className="font-semibold text-lg text-red-600 dark:text-red-400">{formatCurrency(document.underpaymentAmount)}</p>
                    </div>
                  </div>
                )}

                {!hasUnderpayment && (
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-md bg-primary/10">
                      <DollarSign className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Amount</p>
                      <p className="font-semibold text-lg">{formatCurrency(document.amount)}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-md bg-primary/10">
                    <Calendar className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Created</p>
                    <p className="font-medium">{formatRelativeTime(document.createdAt)}</p>
                  </div>
                </div>
              </div>

              {/* Success Message */}
              {document.status === "succeeded" && (
                <div className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-md",
                  config.bgColor
                )}>
                  <CheckCircle2 className={cn("h-4 w-4", config.color)} />
                  <span className={cn("text-sm font-medium", config.color)}>
                    Payment received successfully
                  </span>
                </div>
              )}

              {/* Additional Info */}
              {document.rulesApplied && document.rulesApplied.length > 0 && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  <span>{document.rulesApplied.length} rule(s) applied</span>
                </div>
              )}
            </div>

            {/* Arrow Icon */}
            <div className="opacity-0 group-hover:opacity-100 transition-opacity">
              <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
          </div>
        </CardContent>
      </Link>
    </Card>
  );
}



