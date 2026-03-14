import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PerformanceMetrics } from "@/components/reports/PerformanceMetrics";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ReportsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">
            Track performance and revenue recovered
          </p>
        </div>

        <PerformanceMetrics />

        <Card>
          <CardHeader>
            <CardTitle>Revenue Overview</CardTitle>
            <CardDescription>
              Track your revenue recovery over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Charts and detailed analytics will be available here.
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}



