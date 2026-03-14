import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getDocuments, updateDocument } from "@/lib/api/documents";
import { DocumentFilters, DocumentStatus } from "@/lib/types/document";
import { formatCurrency } from "@/lib/utils/currency";
import { formatDate, formatDateTime } from "@/lib/utils/date";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Download, ExternalLink, FileText, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Link } from "wouter";

interface DocumentListProps {
  filters?: DocumentFilters;
  page: number;
  onPageChange: (page: number) => void;
}

const statusColors: Record<DocumentStatus, string> = {
  [DocumentStatus.NOT_SUBMITTED]: "bg-gray-100 text-gray-700 border-gray-300",
  [DocumentStatus.IN_PROGRESS]: "bg-yellow-100 text-yellow-800 border-yellow-300",
  [DocumentStatus.FAILED]: "bg-red-100 text-red-700 border-red-300",
  [DocumentStatus.CANCELLED]: "bg-red-900 text-white border-red-900",
  [DocumentStatus.DECLINED]: "bg-red-100 text-red-700 border-red-300",
  [DocumentStatus.SUCCEEDED]: "bg-green-100 text-green-700 border-green-300",
};

const statusLabels: Record<DocumentStatus, string> = {
  [DocumentStatus.SUCCEEDED]: "Succeeded",
  [DocumentStatus.IN_PROGRESS]: "In Progress",
  [DocumentStatus.FAILED]: "Failed",
  [DocumentStatus.CANCELLED]: "Cancelled",
  [DocumentStatus.DECLINED]: "Declined",
  [DocumentStatus.NOT_SUBMITTED]: "Not Submitted",
};

const LIMIT = 15;

export function DocumentList({ filters, page, onPageChange }: DocumentListProps) {
  const queryClient = useQueryClient();
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["/documents", { ...filters, limit: LIMIT, offset: page * LIMIT }],
    queryFn: () => getDocuments({ ...filters, limit: LIMIT, offset: page * LIMIT }),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateDocument(id, { status }),
    onSuccess: () => {
      toast.success("Status updated");
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
      setUpdatingId(null);
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to update status");
      setUpdatingId(null);
    },
  });

  const documents = Array.isArray(data) ? data : (data?.items || []);
  const total = Array.isArray(data) ? data.length : (data?.total || 0);
  const hasMore = Array.isArray(data) ? false : (data?.hasMore || false);
  const totalPages = Math.ceil(total / LIMIT);

  const handleStatusChange = (documentId: string, newStatus: string) => {
    setUpdatingId(documentId);
    updateStatusMutation.mutate({ id: documentId, status: newStatus });
  };

  const getStatusMeta = (status: string) => {
    const normalized = (Object.values(DocumentStatus) as string[]).includes(status)
      ? (status as DocumentStatus)
      : DocumentStatus.NOT_SUBMITTED;
    return {
      color: statusColors[normalized],
      label: statusLabels[normalized],
      value: normalized,
    };
  };

  const handleDownloadPDF = async (document: any) => {
    toast.info("Generating PDF...");

    try {
      const { jsPDF } = await import("jspdf");
      
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
      });

      let yPos = 20;
      const pageWidth = 210;
      const margin = 20;
      const contentWidth = pageWidth - (margin * 2);

      pdf.setFontSize(24);
      pdf.setFont('helvetica', 'bold');
      pdf.text(document.name || "Document Details", margin, yPos);
      yPos += 10;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      pdf.setTextColor(100, 100, 100);
      pdf.text(`ID: ${document.id}`, margin, yPos);
      yPos += 15;

      if (document.notes || document.reasoning) {
        pdf.setFillColor(240, 248, 255);
        pdf.rect(margin - 5, yPos - 5, contentWidth + 10, 0, 'F');
        
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(37, 99, 235);
        pdf.text("AI Analysis", margin, yPos);
        yPos += 8;

        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        pdf.setTextColor(0, 0, 0);
        const analysisText = document.reasoning || document.notes || '';
        const splitAnalysis = pdf.splitTextToSize(analysisText, contentWidth);
        pdf.text(splitAnalysis, margin, yPos);
        yPos += (splitAnalysis.length * 5) + 15;
      }

      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.setTextColor(0, 0, 0);
      pdf.text("Payment Breakdown", margin, yPos);
      yPos += 10;

      pdf.setFillColor(245, 245, 245);
      pdf.rect(margin, yPos, (contentWidth / 2) - 5, 30, 'F');
      pdf.setFontSize(10);
      pdf.setTextColor(100, 100, 100);
      pdf.text("Billing Record Amount", margin + 5, yPos + 7);
      pdf.setFontSize(8);
      pdf.text("What was actually paid", margin + 5, yPos + 11);
      pdf.setFontSize(16);
      pdf.setFont('helvetica', 'bold');
      pdf.setTextColor(0, 0, 0);
      pdf.text(formatCurrency(document.receiptAmount || 0), margin + 5, yPos + 22);

      pdf.setFillColor(239, 246, 255);
      pdf.rect(margin + (contentWidth / 2) + 5, yPos, (contentWidth / 2) - 5, 30, 'F');
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(10);
      pdf.setTextColor(100, 100, 100);
      pdf.text("Contract Amount", margin + (contentWidth / 2) + 10, yPos + 7);
      pdf.setFontSize(8);
      pdf.text("What should have been paid", margin + (contentWidth / 2) + 10, yPos + 11);
      pdf.setFontSize(16);
      pdf.setFont('helvetica', 'bold');
      pdf.setTextColor(37, 99, 235);
      pdf.text(formatCurrency(document.contractAmount || 0), margin + (contentWidth / 2) + 10, yPos + 22);
      yPos += 40;

      const underpayment = document.underpaymentAmount ?? document.amount;
      if (underpayment > 0) {
        pdf.setFillColor(254, 242, 242);
        pdf.setDrawColor(252, 165, 165);
        pdf.setLineWidth(0.5);
        pdf.rect(margin, yPos, contentWidth, 20, 'FD');
        
        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(185, 28, 28);
        pdf.text("Underpayment Detected", margin + 5, yPos + 8);
        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'normal');
        pdf.text("Amount owed based on contract terms", margin + 5, yPos + 13);
        
        pdf.setFontSize(18);
        pdf.setFont('helvetica', 'bold');
        pdf.text(formatCurrency(underpayment), pageWidth - margin - 5, yPos + 13, { align: 'right' });
        yPos += 30;
      } else {
        pdf.setFillColor(240, 253, 244);
        pdf.setDrawColor(134, 239, 172);
        pdf.setLineWidth(0.5);
        pdf.rect(margin, yPos, contentWidth, 20, 'FD');
        
        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(21, 128, 61);
        pdf.text("No Underpayment", margin + 5, yPos + 8);
        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'normal');
        pdf.text("Payment matches contract terms", margin + 5, yPos + 13);
        
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text("All Good", pageWidth - margin - 5, yPos + 13, { align: 'right' });
        yPos += 30;
      }

      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.setTextColor(0, 0, 0);
      pdf.text("Details", margin, yPos);
      yPos += 10;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      pdf.setTextColor(100, 100, 100);
      
      const details = [
        ['Billing Record ID', document.receiptId || '-'],
        ['Contract ID', document.contractId || '-'],
        ['Created', formatDateTime(document.createdAt)],
        ['Last Updated', formatDateTime(document.updatedAt)],
      ];

      if (document.submittedAt) {
        details.push(['Submitted', formatDateTime(document.submittedAt)]);
      }

      details.forEach(([label, value]) => {
        pdf.setFont('helvetica', 'normal');
        pdf.setTextColor(100, 100, 100);
        pdf.text(label, margin, yPos);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(0, 0, 0);
        pdf.text(value, margin + 50, yPos);
        yPos += 7;
      });

      const filename = `${document.name || 'document'}-${document.id.slice(0, 8)}.pdf`;
      pdf.save(filename);
      
      toast.success("PDF downloaded successfully");
    } catch (error) {
      console.error("PDF generation error:", error);
      toast.error(`Failed to generate PDF`);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-destructive">
            Failed to load documents. Please try again.
          </div>
        </CardContent>
      </Card>
    );
  }

  if (documents.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="p-16 text-center">
          <div className="mx-auto w-24 h-24 rounded-full bg-muted flex items-center justify-center mb-6">
            <FileText className="h-12 w-12 text-muted-foreground" />
          </div>
          <h3 className="text-xl font-semibold mb-2">No documents found</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            Documents will appear here when billing records with differences are processed and documents are generated.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Document Name</TableHead>
              <TableHead>Paid</TableHead>
              <TableHead>Should Pay</TableHead>
              <TableHead>Underpayment</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((document) => (
              <TableRow key={document.id}>
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium">
                        {document.name || `Document ${document.id.slice(0, 8)}`}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Billing Record: {document.receiptId ? `${document.receiptId.slice(0, 8)}...` : "Not linked"}
                      </p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="font-medium">
                    {formatCurrency(document.receiptAmount || 0)}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="font-medium text-blue-600">
                    {formatCurrency(document.contractAmount || 0)}
                  </span>
                </TableCell>
                <TableCell>
                  {(document.underpaymentAmount || document.amount) > 0 ? (
                    <span className="text-destructive font-semibold">
                      {formatCurrency(document.underpaymentAmount || document.amount)}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">-</span>
                  )}
                </TableCell>
                <TableCell>
                  {updatingId === document.id ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-muted text-muted-foreground">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      Updating...
                    </span>
                  ) : (
                    <Select
                      value={getStatusMeta(document.status).value}
                      onValueChange={(value) => handleStatusChange(document.id, value)}
                      disabled={updateStatusMutation.isPending}
                    >
                      <SelectTrigger className="w-auto border-0 bg-transparent h-auto p-0 shadow-none focus:ring-0 [&>svg]:ml-1 [&>svg]:h-3 [&>svg]:w-3">
                        <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold cursor-pointer ${getStatusMeta(document.status).color}`}>
                          {getStatusMeta(document.status).label}
                        </span>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={DocumentStatus.NOT_SUBMITTED}>Not Submitted</SelectItem>
                        <SelectItem value={DocumentStatus.IN_PROGRESS}>In Progress</SelectItem>
                        <SelectItem value={DocumentStatus.CANCELLED}>Cancelled</SelectItem>
                        <SelectItem value={DocumentStatus.DECLINED}>Declined</SelectItem>
                        <SelectItem value={DocumentStatus.SUCCEEDED}>Succeeded</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                </TableCell>
                <TableCell>{formatDate(document.createdAt)}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Button asChild size="sm" variant="outline">
                      <Link href={`/dashboard/documents/${document.id}`}>
                        <ExternalLink className="h-4 w-4 mr-1" />
                        View
                      </Link>
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleDownloadPDF(document)}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      PDF
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t">
            <p className="text-sm text-muted-foreground">
              Showing {page * LIMIT + 1}-{Math.min((page + 1) * LIMIT, total)} of {total} documents
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(Math.max(0, page - 1))}
                disabled={page === 0}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(page + 1)}
                disabled={!hasMore}
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
