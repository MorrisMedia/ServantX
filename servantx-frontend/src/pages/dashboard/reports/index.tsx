import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PerformanceMetrics } from "@/components/reports/PerformanceMetrics";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { getDocuments, getDocumentStats } from "@/lib/api/documents";
import { formatCurrency } from "@/lib/utils/currency";

export default function ReportsPage() {
  const { data: stats } = useQuery({
    queryKey: ["/documents/stats"],
    queryFn: () => getDocumentStats(),
  });

  const { data: documentsResponse } = useQuery({
    queryKey: ["/documents/report"],
    queryFn: () => getDocuments({ limit: 100, offset: 0 }),
  });

  const documents = Array.isArray(documentsResponse)
    ? documentsResponse
    : documentsResponse?.items || [];

  const topFindings = [...documents]
    .sort((a, b) => (b.underpaymentAmount || b.amount || 0) - (a.underpaymentAmount || a.amount || 0))
    .slice(0, 5);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">
            Executive-ready view of underpayment exposure, batch progress, and the highest-priority findings.
          </p>
        </div>

        <PerformanceMetrics />

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Executive summary</CardTitle>
              <CardDescription>What a CFO or revenue integrity lead should see first</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>Total flagged exposure: <strong className="text-foreground">{formatCurrency(stats?.totalUnderpayment || 0)}</strong></p>
              <p>Documents reviewed: <strong className="text-foreground">{stats?.total || 0}</strong></p>
              <p>High-confidence successes: <strong className="text-foreground">{stats?.succeeded || 0}</strong></p>
              <p>Needs analyst review: <strong className="text-foreground">{stats?.inProgress || 0}</strong></p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recommended visual report outputs</CardTitle>
              <CardDescription>Needed for the admin/analyst operating model</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>• Exposure by payer and by audit batch</p>
              <p>• Findings by status, confidence, and appeal readiness</p>
              <p>• Trendline across the last 24 months of audits</p>
              <p>• Top root causes with source-of-truth references</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Top findings</CardTitle>
            <CardDescription>Highest-priority claim documents by underpayment amount</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {topFindings.length > 0 ? topFindings.map((doc) => (
              <div key={doc.id} className="rounded-lg border p-4 flex items-start justify-between gap-4">
                <div>
                  <div className="font-medium">{doc.name || `Document ${doc.id.slice(0, 8)}`}</div>
                  <div className="text-sm text-muted-foreground">Status: {doc.status}</div>
                </div>
                <div className="text-right font-semibold text-red-600">
                  {formatCurrency(doc.underpaymentAmount || doc.amount || 0)}
                </div>
              </div>
            )) : <p className="text-sm text-muted-foreground">No findings available yet.</p>}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
