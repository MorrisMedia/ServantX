export interface Rule {
  id: string;
  contractId: string;
  contractName?: string;
  name: string;
  description: string;
  type: "validation" | "comparison" | "document" | "other";
  conditions?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  isActive: boolean;
}

export interface RuleFilters {
  contractId?: string;
  type?: string[];
  isActive?: boolean;
}



