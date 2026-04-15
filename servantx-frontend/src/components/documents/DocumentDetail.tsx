import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { getDocument, submitDocument, updateDocument } from "@/lib/api/documents";
import { DocumentStatus } from "@/lib/types/document";
import { PricingEnginesTable } from "./PricingEnginesTable";
import { formatCurrency } from "@/lib/utils/currency";
import { formatDateTime } from "@/lib/utils/date";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Brain, DollarSign, Download, FileText, Loader2, Pencil, Save, Send, X } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { useLocation } from "wouter";

interface DocumentDetailProps {
  documentId: string;
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

export function DocumentDetail({ documentId }: DocumentDetailProps) {
  const [, setLocation] = useLocation();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [editForm, setEditForm] = useState({
    name: "",
    notes: "",
    receiptAmount: 0,
    contractAmount: 0,
    underpaymentAmount: 0,
  });

  const { data: document, isLoading, error } = useQuery({
    queryKey: ["/documents", documentId],
    queryFn: () => getDocument(documentId),
  });

  const submitMutation = useMutation({
    mutationFn: submitDocument,
    onSuccess: () => {
      toast.success("Document submitted successfully");
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
      queryClient.invalidateQueries({ queryKey: ["/documents", documentId] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to submit document");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: typeof editForm) => updateDocument(documentId, data),
    onSuccess: () => {
      toast.success("Document updated successfully");
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
      queryClient.invalidateQueries({ queryKey: ["/documents", documentId] });
      setIsEditing(false);
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to update document");
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: (status: string) => updateDocument(documentId, { status }),
    onSuccess: () => {
      toast.success("Status updated");
      queryClient.invalidateQueries({ queryKey: ["/documents"] });
      queryClient.invalidateQueries({ queryKey: ["/documents", documentId] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to update status");
    },
  });

  const startEditing = () => {
    if (document) {
      setEditForm({
        name: document.name || "",
        notes: document.notes || "",
        receiptAmount: document.receiptAmount || 0,
        contractAmount: document.contractAmount || 0,
        underpaymentAmount: document.underpaymentAmount || document.amount || 0,
      });
      setIsEditing(true);
    }
  };

  const cancelEditing = () => {
    setIsEditing(false);
  };

  const handleSave = () => {
    updateMutation.mutate(editForm);
  };

  const handleStatusChange = (newStatus: string) => {
    updateStatusMutation.mutate(newStatus);
  };

  const handleDownloadPDF = async () => {
    if (!document) {
      toast.error("Unable to generate PDF");
      return;
    }

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
      <div className="space-y-6 max-w-4xl mx-auto">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-destructive">
              Failed to load document. Please try again.
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const hasAnalysis = document.notes || document.reasoning;
  const isNotSubmitted = document.status === "not_submitted";
  const isSubmitted = document.status !== "not_submitted";

  return (
    <div ref={contentRef} className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => setLocation("/dashboard/documents")} className="no-print">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {document.name || "Document Details"}
            </h1>
            <p className="text-sm text-muted-foreground">ID: {document.id.slice(0, 12)}...</p>
          </div>
        </div>
        <div className="flex items-center gap-2 no-print">
          {!isEditing && (
            <>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleDownloadPDF();
                }}
                type="button"
              >
                <Download className="h-4 w-4 mr-1" />
                Download PDF
              </Button>
              <Button variant="outline" size="sm" onClick={startEditing}>
                <Pencil className="h-4 w-4 mr-1" />
                Edit
              </Button>
            </>
          )}
          {isNotSubmitted ? (
            <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${statusColors[document.status as DocumentStatus]}`}>
              {statusLabels[document.status as DocumentStatus]}
            </span>
          ) : updateStatusMutation.isPending ? (
            <span className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-muted text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Updating...
            </span>
          ) : (
            <Select value={document.status} onValueChange={handleStatusChange} disabled={updateStatusMutation.isPending}>
              <SelectTrigger className="w-auto border-0 bg-transparent h-auto p-0 shadow-none focus:ring-0 [&>svg]:ml-1 [&>svg]:h-3 [&>svg]:w-3">
                <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold cursor-pointer ${statusColors[document.status as DocumentStatus]}`}>
                  {statusLabels[document.status as DocumentStatus] || document.status}
                </span>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={DocumentStatus.IN_PROGRESS}>In Progress</SelectItem>
                <SelectItem value={DocumentStatus.CANCELLED}>Cancelled</SelectItem>
                <SelectItem value={DocumentStatus.DECLINED}>Declined</SelectItem>
                <SelectItem value={DocumentStatus.SUCCEEDED}>Succeeded</SelectItem>
              </SelectContent>
            </Select>
          )}
        </div>
      </div>

      {isEditing ? (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Pencil className="h-5 w-5" />
              Edit Document
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Document Name</Label>
              <Input
                id="name"
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                placeholder="Enter document name"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="receiptAmount">Billing Record Amount</Label>
                <Input
                  id="receiptAmount"
                  type="number"
                  step="0.01"
                  value={editForm.receiptAmount}
                  onChange={(e) => setEditForm({ ...editForm, receiptAmount: parseFloat(e.target.value) || 0 })}
                />
                <p className="text-xs text-muted-foreground">What was actually billed</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="contractAmount">Contract Amount</Label>
                <Input
                  id="contractAmount"
                  type="number"
                  step="0.01"
                  value={editForm.contractAmount}
                  onChange={(e) => setEditForm({ ...editForm, contractAmount: parseFloat(e.target.value) || 0 })}
                />
                <p className="text-xs text-muted-foreground">What should have been paid</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="underpaymentAmount">Underpayment Amount</Label>
                <Input
                  id="underpaymentAmount"
                  type="number"
                  step="0.01"
                  value={editForm.underpaymentAmount}
                  onChange={(e) => setEditForm({ ...editForm, underpaymentAmount: parseFloat(e.target.value) || 0 })}
                />
                <p className="text-xs text-muted-foreground">Amount owed</p>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notes / AI Analysis</Label>
              <Textarea
                id="notes"
                value={editForm.notes}
                onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                placeholder="Enter notes or analysis"
                rows={4}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={cancelEditing} disabled={updateMutation.isPending}>
                <X className="h-4 w-4 mr-1" />
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={updateMutation.isPending}>
                {updateMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-1" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {hasAnalysis && (
            <Card className="border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/20">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Brain className="h-5 w-5 text-blue-600" />
                  AI Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {document.reasoning || document.notes}
                </p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <DollarSign className="h-5 w-5" />
                Payment Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg border bg-muted/30">
                  <p className="text-sm text-muted-foreground mb-1">Billing Record Amount</p>
                  <p className="text-xs text-muted-foreground mb-2">What the payer actually paid</p>
                  <p className="text-2xl font-bold">{formatCurrency(document.receiptAmount || 0)}</p>
                </div>
                <div className="p-4 rounded-lg border bg-blue-50 dark:bg-blue-950/30">
                  <p className="text-sm text-muted-foreground mb-1">Contract Amount</p>
                  <p className="text-xs text-muted-foreground mb-2">What they should have paid per contract</p>
                  <p className="text-2xl font-bold text-blue-600">{formatCurrency(document.contractAmount || 0)}</p>
                </div>
              </div>

              {(document.underpaymentAmount !== undefined && document.underpaymentAmount > 0) || document.amount > 0 ? (
                <div className="p-4 rounded-lg border-2 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/30">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-red-700 dark:text-red-400">Underpayment Detected</p>
                      <p className="text-xs text-red-600/70 dark:text-red-400/70">Amount owed based on contract terms</p>
                    </div>
                    <p className="text-3xl font-bold text-red-600 dark:text-red-400">{formatCurrency(document.underpaymentAmount ?? document.amount)}</p>
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-lg border-2 border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/30">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-green-700 dark:text-green-400">No Underpayment</p>
                      <p className="text-xs text-green-600/70 dark:text-green-400/70">Payment matches contract terms</p>
                    </div>
                    <p className="text-xl font-bold text-green-600 dark:text-green-400">All Good</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <PricingEnginesTable
            notesPayload={(document as any).notes_payload}
            primaryEngine={(document as any).repricing_method}
          />

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <FileText className="h-5 w-5" />
                Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-x-8 gap-y-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Billing Record ID</p>
                  <p className="font-mono">{document.receiptId?.slice(0, 12) || "-"}...</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Contract ID</p>
                  <p className="font-mono">{document.contractId?.slice(0, 12) || "-"}...</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Created</p>
                  <p>{formatDateTime(document.createdAt)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Last Updated</p>
                  <p>{formatDateTime(document.updatedAt)}</p>
                </div>
                {document.submittedAt && (
                  <div>
                    <p className="text-muted-foreground">Submitted</p>
                    <p>{formatDateTime(document.submittedAt)}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {isNotSubmitted && (
            <Card className="no-print">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Ready to submit</p>
                    <p className="text-sm text-muted-foreground">
                      Submit this document for processing
                    </p>
                  </div>
                  <Button
                    onClick={() => submitMutation.mutate(document.id)}
                    disabled={submitMutation.isPending}
                  >
                    {submitMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        Submit Document
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {isSubmitted && (
            <Card className="no-print">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Update Status</p>
                    <p className="text-sm text-muted-foreground">
                      Change the status of this document
                    </p>
                  </div>
                  {updateStatusMutation.isPending ? (
                    <span className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-semibold bg-muted text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Updating...
                    </span>
                  ) : (
                    <Select value={document.status} onValueChange={handleStatusChange} disabled={updateStatusMutation.isPending}>
                      <SelectTrigger className="w-[180px]">
                        <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${statusColors[document.status as DocumentStatus]}`}>
                          {statusLabels[document.status as DocumentStatus] || document.status}
                        </span>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={DocumentStatus.IN_PROGRESS}>In Progress</SelectItem>
                        <SelectItem value={DocumentStatus.CANCELLED}>Cancelled</SelectItem>
                        <SelectItem value={DocumentStatus.DECLINED}>Declined</SelectItem>
                        <SelectItem value={DocumentStatus.SUCCEEDED}>Succeeded</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
