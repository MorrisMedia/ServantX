import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { buildAppealPacket } from "@/lib/api/appeals";
import { getAnalysisPatterns, getAnalysisSummary, getCoverageReport } from "@/lib/api/analysis";
import { getBatchDocuments, getBatchStatus } from "@/lib/api/batches";
import { getRatesStatus } from "@/lib/api/rates";
import { formatCurrency } from "@/lib/utils/currency";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, FileStack, Loader2, WandSparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { useLocation } from "wouter";

function parseBatchIdFromLocation(location: string): string {
  const query = location.includes("?") ? location.split("?")[1] : "";
  const params = new URLSearchParams(query);
  return params.get("batchId") || "";
}

export default function AuditWorkflowPage() {
  const [location] = useLocation();
  const [batchId, setBatchId] = useState<string>(() => parseBatchIdFromLocation(location));
  const [operationalNotes, setOperationalNotes] = useState("");

  const summaryQuery = useQuery({
    queryKey: ["/analysis", batchId],
    queryFn: () => getAnalysisSummary(batchId || undefined),
    enabled: !!batchId,
  });

  const patternsQuery = useQuery({
    queryKey: ["/analysis/patterns", batchId],
    queryFn: () => getAnalysisPatterns(batchId || undefined),
    enabled: !!batchId,
  });

  const batchStatusQuery = useQuery({
    queryKey: ["/batches/status", batchId],
    queryFn: () => getBatchStatus(batchId),
    enabled: !!batchId,
  });

  const batchDocumentsQuery = useQuery({
    queryKey: ["/batches/documents", batchId],
    queryFn: () => getBatchDocuments(batchId),
    enabled: !!batchId,
  });

  const ratesStatusQuery = useQuery({
    queryKey: ["/admin/rates/status"],
    queryFn: getRatesStatus,
    retry: false,
  });

  const coverageQuery = useQuery({
    queryKey: ["/analysis/coverage", batchId],
    queryFn: () => getCoverageReport(batchId || undefined),
    enabled: !!batchId,
  });

  const buildAppealMutation = useMutation({
    mutationFn: () => buildAppealPacket({ batchId }),
    onSuccess: () => {
      toast.success("Appeal packet build started");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to build appeal packet");
    },
  });

  const serviceLineRows = useMemo(() => {
    const docs = batchDocumentsQuery.data?.items || [];
    const flattened: Array<{
      docId: string;
      cpt: string;
      modifier: string;
      pos: string;
      locality: string;
      expected: number;
      paid: number;
      variance: number;
    }> = [];
    docs.forEach((doc) => {
      const repricing = doc.repricingSummary as { line_results?: any[] } | undefined;
      (repricing?.line_results || []).forEach((line: any) => {
        flattened.push({
          docId: doc.id,
          cpt: line.cpt_hcpcs || "UNKNOWN",
          modifier: (line.modifiers || [])[0] || "-",
          pos: line.place_of_service || "-",
          locality: line.locality_code || "-",
          expected: Number(line.expected_allowed || 0),
          paid: Number(line.actual_paid || 0),
          variance: Number(line.variance_amount || 0),
        });
      });
    });
    return flattened;
  }, [batchDocumentsQuery.data]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Audit Workflow</h1>
          <p className="text-muted-foreground">
            Medicare + TX Medicaid underpayment workflow from 835 ingest to appeal packet generation.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Batch Context</CardTitle>
            <CardDescription>Enter or paste a batch ID to inspect a specific 835 workflow run.</CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Input
              placeholder="Batch ID"
              value={batchId}
              onChange={(e) => setBatchId(e.target.value)}
            />
            <Button
              onClick={() => {
                if (!batchId) {
                  toast.error("Batch ID is required");
                  return;
                }
                summaryQuery.refetch();
                patternsQuery.refetch();
                batchStatusQuery.refetch();
                batchDocumentsQuery.refetch();
              }}
            >
              Load
            </Button>
          </CardContent>
        </Card>

        {!batchId ? (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              Provide a batch ID to populate the workflow tabs.
            </CardContent>
          </Card>
        ) : (
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="flex flex-wrap h-auto">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="claims">Claims</TabsTrigger>
              <TabsTrigger value="service-lines">Service Lines</TabsTrigger>
              <TabsTrigger value="patterns">Patterns</TabsTrigger>
              <TabsTrigger value="appeals">Appeals</TabsTrigger>
              <TabsTrigger value="data-sources">Data Sources</TabsTrigger>
              <TabsTrigger value="notes">Notes</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle>Total Recoverable</CardTitle>
                  </CardHeader>
                  <CardContent className="text-2xl font-bold">
                    {formatCurrency(summaryQuery.data?.totalVariance || 0)}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Claims Flagged</CardTitle>
                  </CardHeader>
                  <CardContent className="text-2xl font-bold">{summaryQuery.data?.claimsFlagged || 0}</CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Batch Status</CardTitle>
                  </CardHeader>
                  <CardContent className="text-2xl font-bold">{batchStatusQuery.data?.status || "Unknown"}</CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="claims">
              <Card>
                <CardHeader>
                  <CardTitle>Claims</CardTitle>
                  <CardDescription>Claim-level documents generated from CLP loops.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(batchDocumentsQuery.data?.items || []).map((doc) => (
                    <div key={doc.id} className="rounded border p-3 text-sm">
                      <div className="font-medium">{doc.name || doc.id}</div>
                      <div className="text-muted-foreground">
                        Status: {doc.status} | Payer: {doc.payerKey || "-"} | DOS: {doc.dosStart || "-"} to {doc.dosEnd || "-"} | Variance: {formatCurrency(doc.underpaymentAmount || 0)}
                      </div>
                    </div>
                  ))}
                  {(batchDocumentsQuery.data?.items || []).length === 0 && (
                    <div className="text-sm text-muted-foreground">No claim documents returned for this batch.</div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="service-lines">
              <Card>
                <CardHeader>
                  <CardTitle>Service Lines</CardTitle>
                  <CardDescription>Grouped service-line repricing output (CPT / modifier / POS / locality).</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {serviceLineRows.slice(0, 100).map((line, idx) => (
                    <div key={`${line.docId}-${idx}`} className="rounded border p-2 text-sm">
                      {line.cpt} {line.modifier !== "-" ? `-${line.modifier}` : ""} | POS {line.pos} | Locality {line.locality} | Paid {formatCurrency(line.paid)} | Expected {formatCurrency(line.expected)} | Variance {formatCurrency(line.variance)}
                    </div>
                  ))}
                  {serviceLineRows.length === 0 && <div className="text-sm text-muted-foreground">No service-line repricing data yet.</div>}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="patterns">
              <Card>
                <CardHeader>
                  <CardTitle>Patterns</CardTitle>
                  <CardDescription>Top payer/CPT/modifier/POS/locality clusters by total variance.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {(patternsQuery.data || []).slice(0, 25).map((pattern, idx) => (
                    <div key={idx} className="rounded border p-2 text-sm">
                      {pattern.payerKey} | {pattern.cptHcpcs} | {pattern.modifier || "-"} | POS {pattern.placeOfService || "-"} | Locality {pattern.localityCode || "-"} | Count {pattern.claimCount} | Variance {formatCurrency(pattern.totalVariance)}
                    </div>
                  ))}
                  {(patternsQuery.data || []).length === 0 && <div className="text-sm text-muted-foreground">No patterns available yet.</div>}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="appeals">
              <Card>
                <CardHeader>
                  <CardTitle>Appeals</CardTitle>
                  <CardDescription>Build payer-ready appeal packet artifacts from current batch filters.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button onClick={() => buildAppealMutation.mutate()} disabled={buildAppealMutation.isPending}>
                    {buildAppealMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Building Appeal Packet...
                      </>
                    ) : (
                      <>
                        <WandSparkles className="h-4 w-4 mr-2" />
                        Build Appeal Packet
                      </>
                    )}
                  </Button>
                  {buildAppealMutation.data?.packet && (
                    <pre className="rounded border p-3 text-xs overflow-auto">
                      {JSON.stringify(buildAppealMutation.data.packet, null, 2)}
                    </pre>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="data-sources">
              <Card>
                <CardHeader>
                  <CardTitle>Data Sources</CardTitle>
                  <CardDescription>Rate version coverage and ingestion state.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {ratesStatusQuery.error ? (
                    <div className="text-sm text-muted-foreground flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      Rate status unavailable for this account (admin endpoint).
                    </div>
                  ) : (
                    <>
                      <div className="text-sm font-medium">Coverage Quality</div>
                      <pre className="rounded border p-3 text-xs overflow-auto">
                        {JSON.stringify(coverageQuery.data || {}, null, 2)}
                      </pre>
                      <div className="text-sm font-medium">Coverage</div>
                      <pre className="rounded border p-3 text-xs overflow-auto">
                        {JSON.stringify(ratesStatusQuery.data?.coverage || {}, null, 2)}
                      </pre>
                      <div className="text-sm font-medium">Loaded Versions</div>
                      <pre className="rounded border p-3 text-xs overflow-auto">
                        {JSON.stringify(ratesStatusQuery.data?.versions || [], null, 2)}
                      </pre>
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="notes">
              <Card>
                <CardHeader>
                  <CardTitle>Notes</CardTitle>
                  <CardDescription>Operational notes for payer/provider follow-up.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Textarea
                    value={operationalNotes}
                    onChange={(e) => setOperationalNotes(e.target.value)}
                    placeholder="Capture follow-up actions, payer requirements, and escalation notes..."
                    rows={8}
                  />
                  <div className="text-xs text-muted-foreground flex items-center gap-2">
                    <FileStack className="h-3 w-3" />
                    Local note scratchpad for this session. Persisted audit notes endpoint can be added next.
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}
      </div>
    </DashboardLayout>
  );
}
