import { useQuery } from "@tanstack/react-query";
import { getContracts } from "@/lib/api/contracts";
import type { Contract } from "@/lib/types/contract";

/**
 * Hook to check if the current user has uploaded a contract
 * @returns { hasContract: boolean, isLoading: boolean, contract: Contract | null }
 */
export function useContractCheck() {
  const { data: contracts, isLoading } = useQuery({
    queryKey: ["/contracts"],
    queryFn: getContracts,
    retry: 1,
    staleTime: 30000, // Cache for 30 seconds
  });

  const hasContract = contracts && contracts.length > 0;
  const contract = hasContract ? contracts[0] : null;

  return {
    hasContract: !!hasContract,
    isLoading,
    contract,
  };
}

