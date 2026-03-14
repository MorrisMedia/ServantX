import { useQuery } from "@tanstack/react-query";
import { getDocumentStats } from "@/lib/api/documents";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils/currency";
import { DollarSign, FileText, CheckCircle2, XCircle, Clock } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function PerformanceMetrics() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["/documents/stats"],
    queryFn: () => getDocumentStats(),
  });

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-8 w-1/2 mb-2" />
              <Skeleton className="h-4 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const successRate = stats.total > 0 
    ? ((stats.succeeded / stats.total) * 100).toFixed(1)
    : "0";

  const metrics = [
    {
      title: "Total Revenue",
      value: formatCurrency(stats.totalRevenue),
      icon: DollarSign,
      description: "Amount recovered",
      color: "text-green-600",
    },
    {
      title: "Total Documents",
      value: stats.total.toString(),
      icon: FileText,
      description: "All documents",
      color: "text-blue-600",
    },
    {
      title: "Success Rate",
      value: `${successRate}%`,
      icon: CheckCircle2,
      description: `${stats.succeeded} succeeded`,
      color: "text-green-600",
    },
    {
      title: "In Progress",
      value: stats.inProgress.toString(),
      icon: Clock,
      description: "Pending processing",
      color: "text-yellow-600",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
              <Icon className={`h-4 w-4 ${metric.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <CardDescription className="mt-1">{metric.description}</CardDescription>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}



