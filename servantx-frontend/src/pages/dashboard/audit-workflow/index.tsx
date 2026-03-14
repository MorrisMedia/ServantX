import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { getAnalysisPatterns, getAnalysisSummary, getCoverageReport } from "@/lib/api/analysis";
import { buildAppealPacket } from "@/lib/api/appeals";
import { getBatchDocuments, getBatchStatus } from "@/lib/api/batches";
import { ensureDefaultProject, createFormalAuditRun, verifyProject } from "@/lib/api/projects";
import { getRatesStatus } from "@/lib/api/rates";
import { formatCurrency } from "@/lib/utils/currency";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, FileStack, Loader2, ShieldCheck, WandSparkles } from "lucide-react";
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

  const projectQuery = useQuery({
    queryKey: ["/projects/default"],
    queryFn: ensureDefaultProject,
  });

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
    onSuccess: () => toast.success("Appeal packet build started"),
    onError: (err: Error) => toast.error(err.message || "Failed to build appeal packet"),
  });

  const verifyMutation = useMutation({
    mutationFn: async () => {
      if (!projectQuery.data?.id) throw new Error("No project workspace available");
      return verifyProject(projectQuery.data.id, batchId || undefined);
    },
    onSuccess: () => toast.success("Truth verification completed"),
    onError: (err: Error) => toast.error(err.message || "Failed to verify project truth"),
  });

  const auditMutation = useMutation({
    mutationFn: async () => {
      if (!projectQuery.data?.id) throw new Error("No project workspace available");
      return createFormalAuditRun(projectQuery.data.id, { batchRunId: batchId || undefined });
    },
    onSuccess: () => toast.success("Formal audit run created"),
    onError: (err: Error) => toast.error(err.message || "Failed to create audit run"),
  });

  const serviceLineRows = useMemo(() => {
    const docs = batchDocumentsQuery.data?.items || [];
    const flattened: Array<{ docId: string; cpt: string; modifier: string; pos: string; locality: string; expected: number; paid: number; variance: number }> = [];
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
          <p className="text-muted-foreground">Project-scoped audit workspace with verification and formal audit runs on top of deterministic repricing.</p>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Project Workspace</CardTitle>
              <CardDescription>Default medical-audit project spine for this account.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div><span className="font-medium">Name:</span> {projectQuery.data?.name || "Loading..."}</div>
              <div><span className="font-medium">Slug:</span> {projectQuery.data?.slug || "-"}</div>
              <div><span className="font-medium">DuckDB:</span> {projectQuery.data?.workspaceDuckdbPath || "-"}</div>
              <div><span className="font-medium">Storage Prefix:</span> {projectQuery.data?.storagePrefix || "-"}</div>
              <div><span className="font-medium">Workspace Docs:</span> {projectQuery.data?.workspaceSummary?.documentCount ?? 0}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Batch Context</CardTitle>
              <CardDescription>Paste a batch ID to inspect a specific 835 workflow run.</CardDescription>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Input placeholder="Batch ID" value={batchId} onChange={(e) => setBatchId(e.target.value)} />
              <Button onClick={() => {
                if (!batchId) return toast.error("Batch ID is required");
                summaryQuery.refetch();
                patternsQuery.refetch();
                batchStatusQuery.refetch();
                batchDocumentsQuery.refetch();
              }}>Load</Button>
            </CardContent>
          </Card>
        </div>

        {!batchId ? (
          <Card><CardContent className="p-8 text-center text-muted-foreground">Provide a batch ID to populate the workflow tabs.</CardContent></Card>
        ) : (
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="flex flex-wrap h-auto">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="claims">Claims</TabsTrigger>
              <TabsTrigger value="service-lines">Service Lines</TabsTrigger>
              <TabsTrigger value="patterns">Patterns</TabsTrigger>
              <TabsTrigger value="verification">Verification</TabsTrigger>
              <TabsTrigger value="appeals">Appeals</TabsTrigger>
              <TabsTrigger value="data-sources">Data Sources</TabsTrigger>
              <TabsTrigger value="notes">Notes</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <div className="grid gap-4 md:grid-cols-4">
                <Card><CardHeader><CardTitle>Total Recoverable</CardTitle></CardHeader><CardContent className="text-2xl font-bold">{formatCurrency(summaryQuery.data?.totalVariance || 0)}</CardContent></Card>
                <Card><CardHeader><CardTitle>Claims Flagged</CardTitle></CardHeader><CardContent className="text-2xl font-bold">{summaryQuery.data?.claimsFlagged || 0}</CardContent></Card>
                <Card><CardHeader><CardTitle>Batch Status</CardTitle></CardHeader><CardContent className="text-2xl font-bold">{batchStatusQuery.data?.status || "Unknown"}</CardContent></Card>
                <Card><CardHeader><CardTitle>Project</CardTitle></CardHeader><CardContent className="text-2xl font-bold">{projectQuery.data?.slug || "-"}</CardContent></Card>
              </div>
            </TabsContent>

            <TabsContent value="claims">
              <Card><CardHeader><CardTitle>Claims</CardTitle><CardDescription>Claim-level documents generated from CLP loops.</CardDescription></CardHeader><CardContent className="space-y-3">{(batchDocumentsQuery.data?.items || []).map((doc) => <div key={doc.id} className="rounded border p-3 text-sm"><div className="font-medium">{doc.name || doc.id}</div><div className="text-muted-foreground">Status: {doc.status} | Project: {doc.projectId || "-"} | Payer: {doc.payerKey || "-"} | Variance: {formatCurrency(doc.underpaymentAmount || 0)}</div></div>)}{(batchDocumentsQuery.data?.items || []).length === 0 && <div className="text-sm text-muted-foreground">No claim documents returned for this batch.</div>}</CardContent></Card>
            </TabsContent>

            <TabsContent value="service-lines">
              <Card><CardHeader><CardTitle>Service Lines</CardTitle><CardDescription>Grouped repricing output by CPT / modifier / POS / locality.</CardDescription></CardHeader><CardContent className="space-y-2">{serviceLineRows.slice(0, 100).map((line, idx) => <div key={`${line.docId}-${idx}`} className="rounded border p-2 text-sm">{line.cpt} {line.modifier !== "-" ? `-${line.modifier}` : ""} | POS {line.pos} | Locality {line.locality} | Paid {formatCurrency(line.paid)} | Expected {formatCurrency(line.expected)} | Variance {formatCurrency(line.variance)}</div>)}{serviceLineRows.length === 0 && <div className="text-sm text-muted-foreground">No service-line repricing data yet.</div>}</CardContent></Card>
            </TabsContent>

            <TabsContent value="patterns">
              <Card><CardHeader><CardTitle>Patterns</CardTitle><CardDescription>Top payer/CPT/modifier/POS/locality clusters by total variance.</CardDescription></CardHeader><CardContent className="space-y-2">{(patternsQuery.data || []).slice(0, 25).map((pattern, idx) => <div key={idx} className="rounded border p-2 text-sm">{pattern.payerKey} | {pattern.cptHcpcs} | {pattern.modifier || "-"} | POS {pattern.placeOfService || "-"} | Locality {pattern.localityCode || "-"} | Count {pattern.claimCount} | Variance {formatCurrency(pattern.totalVariance)}</div>)}{(patternsQuery.data || []).length === 0 && <div className="text-sm text-muted-foreground">No patterns available yet.</div>}</CardContent></Card>
            </TabsContent>

            <TabsContent value="verification">
              <Card>
                <CardHeader>
                  <CardTitle>Truth Verification + Formal Audit</CardTitle>
                  <CardDescription>Materialize DuckDB workspace, verify evidence integrity, then stamp a formal audit run.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    <Button onClick={() => verifyMutation.mutate()} disabled={verifyMutation.isPending || !projectQuery.data?.id}>
                      {verifyMutation.isPending ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Verifying...</> : <><ShieldCheck className="mr-2 h-4 w-4" />Run Truth Verification</>}
                    </Button>
                    <Button variant="secondary" onClick={() => auditMutation.mutate()} disabled={auditMutation.isPending || !projectQuery.data?.id}>
                      {auditMutation.isPending ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Building audit...</> : "Create Formal Audit Run"}
                    </Button>
                  </div>
                  {verifyMutation.data && <pre className="rounded border p-3 text-xs overflow-auto">{JSON.stringify(verifyMutation.data, null, 2)}</pre>}
                  {auditMutation.data && <pre className="rounded border p-3 text-xs overflow-auto">{JSON.stringify(auditMutation.data, null, 2)}</pre>}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="appeals">
              <Card><CardHeader><CardTitle>Appeals</CardTitle><CardDescription>Build payer-ready appeal packet artifacts from current batch filters.</CardDescription></CardHeader><CardContent className="space-y-4"><Button onClick={() => buildAppealMutation.mutate()} disabled={buildAppealMutation.isPending}>{buildAppealMutation.isPending ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Building Appeal Packet...</> : <><WandSparkles className="h-4 w-4 mr-2" />Build Appeal Packet</>}</Button>{buildAppealMutation.data?.packet && <pre className="rounded border p-3 text-xs overflow-auto">{JSON.stringify(buildAppealMutation.data.packet, null, 2)}</pre>}</CardContent></Card>
            </TabsContent>

            <TabsContent value="data-sources">
              <Card><CardHeader><CardTitle>Data Sources</CardTitle><CardDescription>Rate coverage and ingestion state.</CardDescription></CardHeader><CardContent className="space-y-3">{ratesStatusQuery.error ? <div className="text-sm text-muted-foreground flex items-center gap-2"><AlertCircle className="h-4 w-4" />Rate status unavailable for this account.</div> : <><div className="text-sm font-medium">Coverage Quality</div><pre className="rounded border p-3 text-xs overflow-auto">{JSON.stringify(coverageQuery.data || {}, null, 2)}</pre><div className="text-sm font-medium">Coverage</div><pre className="rounded border p-3 text-xs overflow-auto">{JSON.stringify(ratesStatusQuery.data?.coverage || {}, null, 2)}</pre><div className="text-sm font-medium">Loaded Versions</div><pre className="rounded border p-3 text-xs overflow-auto">{JSON.stringify(ratesStatusQuery.data?.versions || [], null, 2)}</pre></>}</CardContent></Card>
            </TabsContent>

            <TabsContent value="notes">
              <Card><CardHeader><CardTitle>Notes</CardTitle><CardDescription>Operational notes for payer/provider follow-up.</CardDescription></CardHeader><CardContent className="space-y-3"><Textarea value={operationalNotes} onChange={(e) => setOperationalNotes(e.target.value)} placeholder="Capture follow-up actions, payer requirements, and escalation notes..." rows={8} /><div className="text-xs text-muted-foreground flex items-center gap-2"><FileStack className="h-3 w-3" />Scratchpad only. Persisted audit notes can be layered on next.</div></CardContent></Card>
            </TabsContent>
          </Tabs>
        )}
      </div>
    </DashboardLayout>
  );
}
