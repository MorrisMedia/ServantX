import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getROISummary } from "@/lib/api/appeals";
import type { ROIStatusSummary } from "@/lib/types/document";
import { formatCurrency, formatCurrencyCompact } from "@/lib/utils/currency";
import { useQuery } from "@tanstack/react-query";
import { DollarSign, Flag, PercentIcon, TrendingUp } from "lucide-react";

const appealStatusLabels: Record<string, string> = {
  none: "No Appeal",
  identified: "Identified",
  drafted: "Draft Ready",
  filed: "Filed",
  under_review: "Under Review",
  approved: "Approved",
  partial: "Partial Recovery",
  denied: "Denied",
};

const FUNNEL_ORDER = ["identified", "drafted", "filed", "under_review", "approved", "partial", "denied"];

function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  colorClass,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  colorClass: string;
}) {
  return (
    <Card className={`border-l-4 ${colorClass}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
          </div>
          <div className={`h-12 w-12 rounded-full flex items-center justify-center bg-opacity-10 ${colorClass.replace("border-l-", "bg-").replace("-500", "-100")}`}>
            <Icon className={`h-6 w-6 ${colorClass.replace("border-l-", "text-").replace("-500", "-600")}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AppealFunnelBar({ label, count, amount, maxCount }: { label: string; count: number; amount: number; maxCount: number }) {
  const pct = maxCount > 0 ? Math.max(4, Math.round((count / maxCount) * 100)) : 4;
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="w-28 text-sm font-medium text-right text-muted-foreground shrink-0">{label}</div>
      <div className="flex-1 bg-muted rounded-full h-5 relative overflow-hidden">
        <div
          className="h-5 bg-primary/70 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="w-12 text-sm font-semibold text-right shrink-0">{count}</div>
      <div className="w-24 text-sm text-muted-foreground text-right shrink-0">{formatCurrencyCompact(amount)}</div>
    </div>
  );
}

export default function AnalyticsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["/analytics/roi"],
    queryFn: getROISummary,
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-64" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-28 w-full" />)}
          </div>
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="space-y-4">
          <h1 className="text-3xl font-bold tracking-tight">ROI Dashboard</h1>
          <Card>
            <CardContent className="p-6 text-center text-destructive">
              Failed to load ROI data. Please try again.
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  const roi = data!;

  // Build funnel data from by_status, in FUNNEL_ORDER
  const statusMap = new Map<string, ROIStatusSummary>(
    (roi.by_status || []).map((s) => [s.appeal_status, s])
  );
  const funnelItems = FUNNEL_ORDER.map((key) => ({
    key,
    label: appealStatusLabels[key] || key,
    count: statusMap.get(key)?.count ?? 0,
    identified: statusMap.get(key)?.identified ?? 0,
    recovered: statusMap.get(key)?.recovered ?? 0,
  }));
  const maxFunnelCount = Math.max(...funnelItems.map((f) => f.count), 1);

  const recoveryRatePct = (roi.recovery_rate * 100).toFixed(1);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">ROI Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Financial overview of identified underpayments and appeal recovery pipeline
          </p>
        </div>

        {/* KPI cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <KPICard
            title="Total Identified"
            value={formatCurrency(roi.identified_total)}
            subtitle="Underpayments found"
            icon={DollarSign}
            colorClass="border-l-blue-500"
          />
          <KPICard
            title="Total Recovered"
            value={formatCurrency(roi.recovered_total)}
            subtitle="Via approved appeals"
            icon={TrendingUp}
            colorClass="border-l-green-500"
          />
          <KPICard
            title="Recovery Rate"
            value={`${recoveryRatePct}%`}
            subtitle="Recovered / identified"
            icon={PercentIcon}
            colorClass="border-l-purple-500"
          />
          <KPICard
            title="Claims Flagged"
            value={`${roi.total_flagged} / ${roi.total_claims_processed}`}
            subtitle={`${(roi.flag_rate * 100).toFixed(1)}% flag rate`}
            icon={Flag}
            colorClass="border-l-red-500"
          />
        </div>

        {/* Appeal pipeline funnel */}
        <Card>
          <CardHeader>
            <CardTitle>Appeal Pipeline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="flex items-center gap-3 py-1 mb-1 text-xs text-muted-foreground">
              <div className="w-28 text-right shrink-0">Status</div>
              <div className="flex-1" />
              <div className="w-12 text-right shrink-0">Claims</div>
              <div className="w-24 text-right shrink-0">Identified</div>
            </div>
            {funnelItems.map((item) => (
              <AppealFunnelBar
                key={item.key}
                label={item.label}
                count={item.count}
                amount={item.identified}
                maxCount={maxFunnelCount}
              />
            ))}
            {funnelItems.every((f) => f.count === 0) && (
              <p className="text-sm text-muted-foreground text-center py-6">
                No appeal data yet. Generate appeal letters from document detail pages.
              </p>
            )}
          </CardContent>
        </Card>

        {/* By payer table */}
        <Card>
          <CardHeader>
            <CardTitle>Recovery by Payer</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Payer</TableHead>
                  <TableHead className="text-right">Claims</TableHead>
                  <TableHead className="text-right">Identified</TableHead>
                  <TableHead className="text-right">Recovered</TableHead>
                  <TableHead className="text-right">Recovery Rate</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roi.by_payer && roi.by_payer.length > 0 ? (
                  roi.by_payer.map((row) => (
                    <TableRow key={row.payer}>
                      <TableCell className="font-medium">{row.payer || "Unknown"}</TableCell>
                      <TableCell className="text-right">{row.claims}</TableCell>
                      <TableCell className="text-right">{formatCurrencyCompact(row.identified)}</TableCell>
                      <TableCell className="text-right text-green-600 font-medium">{formatCurrencyCompact(row.recovered)}</TableCell>
                      <TableCell className="text-right">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                          row.rate >= 0.5
                            ? "bg-green-100 text-green-700"
                            : row.rate >= 0.2
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-red-100 text-red-700"
                        }`}>
                          {(row.rate * 100).toFixed(0)}%
                        </span>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                      No payer data available yet
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
