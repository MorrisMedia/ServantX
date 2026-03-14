import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { RulesList } from "@/components/rules/RulesList";
import { Card, CardContent } from "@/components/ui/card";
import { getContracts } from "@/lib/api/contracts";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, Info } from "lucide-react";

export default function RulesPage() {
  const { data: contracts, isLoading: isContractsLoading } = useQuery({
    queryKey: ["/contracts"],
    queryFn: getContracts,
  });

  const hasContracts = (contracts?.length || 0) > 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Rules</h1>
          <p className="text-muted-foreground">
            View rules extracted from your contracts
          </p>
        </div>

        <div className="rounded-lg border border-blue-500 bg-blue-500/10 p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-600 mb-1">About Rules</h3>
              <p className="text-sm text-blue-600/80">
                Rules are automatically extracted from your uploaded contracts. These rules help the scanning process identify potential violations when analyzing billing records.
              </p>
            </div>
          </div>
        </div>

        {isContractsLoading ? (
          <Card>
            <CardContent className="p-12 text-center">
              <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Loading contracts...</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                We are preparing your rules from contract content.
              </p>
            </CardContent>
          </Card>
        ) : !hasContracts ? (
          <Card>
            <CardContent className="p-12 text-center">
              <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No Contracts Found</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Upload or seed a contract first. Rules are generated directly from contract content, including synthetic contracts.
              </p>
            </CardContent>
          </Card>
        ) : (
          <RulesList />
        )}
      </div>
    </DashboardLayout>
  );
}



