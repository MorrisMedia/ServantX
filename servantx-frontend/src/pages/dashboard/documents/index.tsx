import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { DocumentList } from "@/components/documents/DocumentList";
import { FilterBar } from "@/components/filters/FilterBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getDocuments, getDocumentStats, markDocumentsBulkDownloaded } from "@/lib/api/documents";
import { getActiveProjectId, setActiveProjectId } from "@/lib/activeProject";
import { useDocumentFilters } from "@/lib/hooks/useFilters";
import { formatCurrency } from "@/lib/utils/currency";
import { formatDateTime } from "@/lib/utils/date";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Clock, Download, FileText, Loader2, TrendingUp } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const { filters, updateFilters, clearFilters } = useDocumentFilters();
  const search = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : new URLSearchParams();
  const queryProjectId = search.get("projectId");
  const activeProjectId = queryProjectId || getActiveProjectId();
  if (queryProjectId) setActiveProjectId(queryProjectId);
  const [page, setPage] = useState(0);
  const [isDownloadingAll, setIsDownloadingAll] = useState(false);
  const [appealStatusFilter, setAppealStatusFilter] = useState<'all' | 'none' | 'identified' | 'drafted' | 'filed' | 'under_review' | 'approved' | 'partial' | 'denied'>('all');

  const { data: stats } = useQuery({
    queryKey: ["/documents/stats", filters, activeProjectId],
    queryFn: () => getDocumentStats({ ...(filters as any), projectId: activeProjectId || undefined } as any),
  });

  const { data: notDownloadedCount } = useQuery({
    queryKey: ["/documents/not-downloaded-count", filters],
    queryFn: async () => {
      const allDocuments = [];
      const batchSize = 100;
      let offset = 0;
      let hasMore = true;

      while (hasMore) {
        const batch = await getDocuments({ ...(filters as any), projectId: activeProjectId || undefined, limit: batchSize, offset } as any);
        const items = Array.isArray(batch) ? batch : (batch?.items || []);
        allDocuments.push(...items);
        
        if (items.length < batchSize) {
          hasMore = false;
        } else {
          offset += batchSize;
        }
      }

      return allDocuments.filter(doc => !doc.isBulkDownloaded).length;
    },
  });

  const statsData = stats || {
    total: 0,
    notSubmitted: 0,
    inProgress: 0,
    succeeded: 0,
    failed: 0,
    totalRevenue: 0,
    totalUnderpayment: 0,
  };

  const handleFiltersChange = () => {
    setPage(0);
  };

  const handleDownloadAll = async () => {
    setIsDownloadingAll(true);
    toast.info("Fetching all documents...");

    try {
      const [JSZip, { jsPDF }] = await Promise.all([
        import("jszip").then(m => m.default),
        import("jspdf")
      ]);

      const allDocuments = [];
      const batchSize = 100;
      let offset = 0;
      let hasMore = true;

      while (hasMore) {
        const batch = await getDocuments({ ...(filters as any), projectId: activeProjectId || undefined, limit: batchSize, offset } as any);
        const items = Array.isArray(batch) ? batch : (batch?.items || []);
        allDocuments.push(...items);
        
        if (items.length < batchSize) {
          hasMore = false;
        } else {
          offset += batchSize;
        }
      }

      const notDownloadedDocuments = allDocuments.filter(doc => !doc.isBulkDownloaded);

      if (allDocuments.length === 0) {
        toast.error("No documents found");
        setIsDownloadingAll(false);
        return;
      }

      if (notDownloadedDocuments.length === 0) {
        toast.info("You've already downloaded all these documents");
        setIsDownloadingAll(false);
        return;
      }

      const documents = notDownloadedDocuments;

      toast.info(`Generating ${documents.length} PDFs...`);
      const zip = new JSZip();

      for (let i = 0; i < documents.length; i++) {
        const document = documents[i];
        
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
        const pdfBlob = pdf.output('blob');
        zip.file(filename, pdfBlob);

        if ((i + 1) % 10 === 0) {
          toast.info(`Generated ${i + 1}/${documents.length} PDFs...`);
        }
      }

      toast.info("Creating zip file...");
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      
      const link = window.document.createElement('a');
      link.href = URL.createObjectURL(zipBlob);
      link.download = `documents-${new Date().toISOString().split('T')[0]}.zip`;
      link.click();
      URL.revokeObjectURL(link.href);
      
      const documentIds = documents.map(doc => doc.id);
      await markDocumentsBulkDownloaded(documentIds);
      
      queryClient.invalidateQueries({ queryKey: ["/documents/not-downloaded-count"] });
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
      
      toast.success(`Successfully downloaded ${documents.length} documents`);
    } catch (error) {
      console.error("Download all error:", error);
      toast.error("Failed to download all documents");
    } finally {
      setIsDownloadingAll(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
            <p className="text-muted-foreground mt-1">
              Documents are automatically generated when billing records are scanned and underpayments are detected
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Documents</p>
                  <p className="text-2xl font-bold mt-1">{statsData.total}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
                  <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-yellow-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">In Progress</p>
                  <p className="text-2xl font-bold mt-1">{statsData.inProgress}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-yellow-100 dark:bg-yellow-900/20 flex items-center justify-center">
                  <Clock className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Succeeded</p>
                  <p className="text-2xl font-bold mt-1">{statsData.succeeded}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center">
                  <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-red-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Underpayment</p>
                  <p className="text-2xl font-bold mt-1 text-red-600 dark:text-red-400">{formatCurrency(statsData.totalUnderpayment || 0)}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-red-600 dark:text-red-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex items-start gap-4">
          <div className="flex-1">
            <FilterBar
              filters={filters}
              updateFilters={updateFilters}
              clearFilters={clearFilters}
              onFiltersChange={handleFiltersChange}
            />
          </div>
          
          <Button
            variant="outline"
            onClick={handleDownloadAll}
            disabled={isDownloadingAll || (notDownloadedCount !== undefined && notDownloadedCount === 0)}
          >
            {isDownloadingAll ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Downloading...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Download All ({notDownloadedCount ?? statsData.total})
              </>
            )}
          </Button>
        </div>

        <DocumentList
          filters={filters}
          page={page}
          onPageChange={setPage}
          appealStatusFilter={appealStatusFilter}
          onAppealStatusFilterChange={setAppealStatusFilter}
        />
      </div>
    </DashboardLayout>
  );
}
