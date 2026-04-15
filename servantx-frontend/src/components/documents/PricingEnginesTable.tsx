import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronDown, ChevronUp, Cpu } from "lucide-react";
import { formatCurrency } from "@/lib/utils/currency";
import type { PricingEngineResult, NotesPayload } from "@/lib/types/document";
import { cn } from "@/lib/utils";

interface PricingEnginesTableProps {
  notesPayload: NotesPayload | string | undefined;
  primaryEngine?: string;
}

function parseNotesPayload(raw: NotesPayload | string | undefined): NotesPayload | null {
  if (!raw) return null;
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw) as NotesPayload;
    } catch {
      return null;
    }
  }
  return raw;
}

export function PricingEnginesTable({ notesPayload, primaryEngine }: PricingEnginesTableProps) {
  const [expandedEngine, setExpandedEngine] = useState<string | null>(null);

  const payload = parseNotesPayload(notesPayload);
  if (!payload) return null;

  const { pricing_comparison, engines_run, pricing_mode } = payload;
  if (!pricing_comparison || pricing_comparison.length === 0) return null;

  const toggleReasoning = (engine: string) => {
    setExpandedEngine(expandedEngine === engine ? null : engine);
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Cpu className="h-5 w-5 text-purple-600" />
          Pricing Engines
        </CardTitle>
        {engines_run && engines_run.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1">
            {engines_run.map((engine) => (
              <span
                key={engine}
                className="inline-flex items-center rounded-md bg-purple-50 border border-purple-200 px-2 py-0.5 text-xs font-medium text-purple-700 dark:bg-purple-950/30 dark:border-purple-800 dark:text-purple-300"
              >
                {engine}
              </span>
            ))}
            {pricing_mode && (
              <span className="inline-flex items-center rounded-md bg-gray-100 border border-gray-200 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300">
                Mode: {pricing_mode}
              </span>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">Engine</th>
                <th className="text-right px-4 py-2.5 font-medium text-muted-foreground">Expected</th>
                <th className="text-right px-4 py-2.5 font-medium text-muted-foreground">Actual Paid</th>
                <th className="text-right px-4 py-2.5 font-medium text-muted-foreground">Variance</th>
                <th className="text-right px-4 py-2.5 font-medium text-muted-foreground">Confidence</th>
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">Rate Source</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {pricing_comparison.map((row: PricingEngineResult) => {
                const isRecommended =
                  primaryEngine
                    ? row.engine.toLowerCase() === primaryEngine.toLowerCase()
                    : false;
                const hasReasoning = !!row.ai_reasoning;
                const isExpanded = expandedEngine === row.engine;

                return (
                  <>
                    <tr
                      key={row.engine}
                      className={cn(
                        "border-b transition-colors",
                        isRecommended
                          ? "bg-blue-50/60 dark:bg-blue-950/20"
                          : "hover:bg-muted/30"
                      )}
                    >
                      <td className="px-4 py-3 font-medium">
                        <div className="flex items-center gap-1.5">
                          {row.engine}
                          {isRecommended && (
                            <span className="inline-flex items-center rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                              primary
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-medium">
                        {formatCurrency(row.expected_payment)}
                      </td>
                      <td className="px-4 py-3 text-right text-muted-foreground">
                        {formatCurrency(row.actual_paid)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={cn("font-semibold", row.variance_amount > 0 ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400")}>
                          {row.variance_amount > 0 ? "+" : ""}
                          {formatCurrency(row.variance_amount)}
                        </span>
                        {row.variance_percent !== undefined && (
                          <span className="block text-xs text-muted-foreground">
                            {row.variance_percent > 0 ? "+" : ""}
                            {row.variance_percent.toFixed(1)}%
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <div className="w-16 bg-gray-200 rounded-full h-1.5 dark:bg-gray-700">
                            <div
                              className="bg-purple-500 h-1.5 rounded-full"
                              style={{ width: `${Math.min(100, row.confidence_score)}%` }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground w-8 text-right">
                            {row.confidence_score}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground font-mono max-w-[140px] truncate">
                        {row.rate_source}
                      </td>
                      <td className="px-4 py-3">
                        {hasReasoning && (
                          <button
                            onClick={() => toggleReasoning(row.engine)}
                            className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-200 transition-colors"
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="h-3.5 w-3.5" />
                                Hide
                              </>
                            ) : (
                              <>
                                <ChevronDown className="h-3.5 w-3.5" />
                                AI Reasoning
                              </>
                            )}
                          </button>
                        )}
                      </td>
                    </tr>
                    {hasReasoning && isExpanded && (
                      <tr key={`${row.engine}-reasoning`} className="bg-purple-50/40 dark:bg-purple-950/10 border-b">
                        <td colSpan={7} className="px-4 py-3">
                          <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap rounded-md border border-purple-100 bg-white/60 dark:border-purple-900/40 dark:bg-black/20 p-3">
                            <p className="text-xs font-medium text-purple-700 dark:text-purple-300 mb-1.5">AI Reasoning — {row.engine}</p>
                            {row.ai_reasoning}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
