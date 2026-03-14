import { API_BASE_URL } from "../api";
import type { Rule, RuleFilters } from "../types/rule";
import { getAccessToken } from "./token";

export async function getRules(filters?: RuleFilters): Promise<Rule[]> {
  const token = getAccessToken();
  const params = new URLSearchParams();
  if (filters?.contractId) params.append("contractId", filters.contractId);
  if (filters?.type) {
    filters.type.forEach((t) => params.append("type", t));
  }
  if (filters?.isActive !== undefined) params.append("isActive", filters.isActive.toString());

  const queryString = params.toString();
  const url = `${API_BASE_URL}/rules${queryString ? `?${queryString}` : ""}`;
  const response = await fetch(url, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) throw new Error(`Failed to fetch rules: ${response.status}`);
  return response.json();
}

export async function getRule(id: string): Promise<Rule> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/rules/${id}`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
  if (!response.ok) throw new Error(`Failed to fetch rule: ${response.status}`);
  return response.json();
}



