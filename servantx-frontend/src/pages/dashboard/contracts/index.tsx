import { ContractList } from "@/components/contracts/ContractList";
import { ContractAIChat } from "@/components/contracts/ContractAIChat";
import { ContractUpload } from "@/components/contracts/ContractUpload";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { getContracts } from "@/lib/api/contracts";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function ContractsPage() {
  const { data: contracts } = useQuery({
    queryKey: ["/contracts"],
    queryFn: getContracts,
    refetchInterval: (query) => {
      const data = query.state.data as Awaited<ReturnType<typeof getContracts>> | undefined;
      return data?.some((contract) => contract.status === "processing") ? 2000 : false;
    },
  });

  const contractCount = contracts?.length ?? 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Contracts</h1>
          <p className="text-muted-foreground">
            Upload and manage your hospital contracts. You can upload multiple contracts.
          </p>
        </div>

        {contractCount === 0 ? (
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-destructive mb-1">No Contract Uploaded</h3>
                <p className="text-sm text-destructive/80">
                  You need to upload a contract before you can proceed. Please upload your contract to continue.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-green-500 bg-green-500/10 p-4">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-green-600 mb-1">Contracts Uploaded</h3>
                <p className="text-sm text-green-600/80">
                  Now you can scan billing records to see if someone violated those contracts.
                </p>
              </div>
            </div>
          </div>
        )}

        <ContractUpload />

        {contractCount > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Uploaded Contracts</h2>
            <ContractList />
          </div>
        )}

        {contractCount > 0 && <ContractAIChat contracts={contracts || []} />}
      </div>
    </DashboardLayout>
  );
}



