import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getCurrentUser } from "@/lib/api/auth";
import { getDocumentStats, getDocuments } from "@/lib/api/documents";
import { DocumentStatus } from "@/lib/types/document";
import { formatCurrency } from "@/lib/utils/currency";
import { formatDate } from "@/lib/utils/date";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Clock, FileText, XCircle } from "lucide-react";
import { Link } from "wouter";

export default function DashboardPage() {
  const { data: user } = useQuery({
    queryKey: ["/auth/me"],
    queryFn: getCurrentUser,
  });

  const { data: stats } = useQuery({
    queryKey: ["/documents/stats"],
    queryFn: () => getDocumentStats(),
  });

  const { data: documents } = useQuery({
    queryKey: ["/documents"],
    queryFn: () => getDocuments(),
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

  // Handle both array and paginated response formats from backend
  const documentsList = documents ? (Array.isArray(documents) ? documents : documents.items || []) : [];

  const getStatusIcon = (status: DocumentStatus) => {
    switch (status) {
      case DocumentStatus.SUCCEEDED:
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case DocumentStatus.IN_PROGRESS:
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case DocumentStatus.FAILED:
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
          <p className="text-muted-foreground">
            Welcome back{user?.name ? `, ${user.name}` : ""}! Here's an overview of your documents.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statsData.total}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">In Progress</CardTitle>
              <Clock className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statsData.inProgress}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Succeeded</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statsData.succeeded}</div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-red-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Underpayment</CardTitle>
              <FileText className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{formatCurrency(statsData.totalUnderpayment || 0)}</div>
            </CardContent>
          </Card>
        </div>

        {/* Documents Table */}
        <Card>
          <CardHeader>
            <CardTitle>Documents</CardTitle>
            <CardDescription>View all documents and their statuses</CardDescription>
          </CardHeader>
          <CardContent>
            {documentsList.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Paid</TableHead>
                    <TableHead>Should Pay</TableHead>
                    <TableHead>Underpayment</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {documentsList.map((document) => (
                    <TableRow key={document.id}>
                      <TableCell>
                        <Link
                          href={`/dashboard/documents/${document.id}`}
                          className="text-sm hover:underline font-medium"
                        >
                          {document.name || `Document ${document.id.slice(0, 8)}`}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(document.status)}
                          <StatusBadge status={document.status} showTooltip={false} />
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        {formatCurrency(document.receiptAmount || 0)}
                      </TableCell>
                      <TableCell className="font-medium text-blue-600">
                        {formatCurrency(document.contractAmount || 0)}
                      </TableCell>
                      <TableCell className="font-medium text-red-600">
                        {formatCurrency(document.underpaymentAmount || document.amount || 0)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">{formatDate(document.createdAt)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No documents found</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

