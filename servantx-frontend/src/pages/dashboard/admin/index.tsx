// servantx-frontend/src/pages/dashboard/admin/index.tsx
import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DollarSign, Users, Zap, BarChart3, RefreshCw } from "lucide-react";
import { getAccessToken } from "@/lib/api/token";

const API = import.meta.env.VITE_API_URL || "https://api.servantx.ai";

function useAdminFetch(path: string) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const token = getAccessToken();
    try {
      const res = await fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${token}` } });
      setData(await res.json());
    } catch {}
    setLoading(false);
  };

  useEffect(() => { load(); }, [path]);
  return { data, loading, reload: load };
}

export default function AdminDashboard() {
  const { data: stats, reload: reloadStats } = useAdminFetch("/admin/stats");
  const { data: costSummary } = useAdminFetch("/admin/costs/summary");
  const { data: costLog } = useAdminFetch("/admin/costs?limit=50");
  const { data: users } = useAdminFetch("/admin/users");
  const { data: apiKeys } = useAdminFetch("/admin/api-keys");

  const [benchmarkDocId, setBenchmarkDocId] = useState("");
  const [benchmarkResult, setBenchmarkResult] = useState<any>(null);
  const [benchmarking, setBenchmarking] = useState(false);

  const runBenchmark = async () => {
    if (!benchmarkDocId) return;
    setBenchmarking(true);
    const token = getAccessToken();
    try {
      const res = await fetch(`${API}/admin/benchmark`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: benchmarkDocId }),
      });
      setBenchmarkResult(await res.json());
    } catch {}
    setBenchmarking(false);
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Admin Dashboard</h1>
            <p className="text-muted-foreground text-sm">System-wide metrics, costs, and configuration</p>
          </div>
          <Button variant="outline" size="sm" onClick={reloadStats}><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
        </div>

        {/* KPI Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Total Hospitals", value: stats.hospitals, icon: <Users className="h-4 w-4" /> },
              { label: "Total Users", value: stats.users, icon: <Users className="h-4 w-4" /> },
              { label: "AI Cost (All Time)", value: `$${Number(stats.ai_cost_total_usd).toFixed(4)}`, icon: <DollarSign className="h-4 w-4" /> },
              { label: "AI Cost (Today)", value: `$${Number(stats.ai_cost_today_usd).toFixed(4)}`, icon: <DollarSign className="h-4 w-4" /> },
              { label: "AI Cost (7 Days)", value: `$${Number(stats.ai_cost_7d_usd).toFixed(4)}`, icon: <BarChart3 className="h-4 w-4" /> },
              { label: "Total AI Calls", value: stats.ai_total_calls, icon: <Zap className="h-4 w-4" /> },
              { label: "Documents", value: stats.documents, icon: <BarChart3 className="h-4 w-4" /> },
              { label: "Batch Runs", value: stats.batch_runs, icon: <BarChart3 className="h-4 w-4" /> },
            ].map((k) => (
              <Card key={k.label}>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">{k.icon}{k.label}</div>
                  <div className="text-xl font-bold">{k.value}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Tabs defaultValue="costs">
          <TabsList>
            <TabsTrigger value="costs">Costs</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="apikeys">API Keys</TabsTrigger>
            <TabsTrigger value="benchmark">Benchmark</TabsTrigger>
          </TabsList>

          {/* Costs tab */}
          <TabsContent value="costs" className="space-y-4">
            {costSummary && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader><CardTitle className="text-sm">By Model</CardTitle></CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader><TableRow>
                        <TableHead>Model</TableHead><TableHead>Calls</TableHead>
                        <TableHead>Cost</TableHead><TableHead>Cache Hits</TableHead>
                      </TableRow></TableHeader>
                      <TableBody>
                        {costSummary.by_model?.map((r: any) => (
                          <TableRow key={r.model}>
                            <TableCell className="font-mono text-xs">{r.model}</TableCell>
                            <TableCell>{r.calls}</TableCell>
                            <TableCell>${Number(r.cost_usd).toFixed(4)}</TableCell>
                            <TableCell>{r.cache_read_tokens?.toLocaleString() ?? 0}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle className="text-sm">By Service</CardTitle></CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader><TableRow>
                        <TableHead>Service</TableHead><TableHead>Calls</TableHead><TableHead>Cost</TableHead>
                      </TableRow></TableHeader>
                      <TableBody>
                        {costSummary.by_service?.map((r: any) => (
                          <TableRow key={r.service}>
                            <TableCell>{r.service}</TableCell>
                            <TableCell>{r.calls}</TableCell>
                            <TableCell>${Number(r.cost_usd).toFixed(4)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              </div>
            )}
            <Card>
              <CardHeader><CardTitle className="text-sm">Recent Calls</CardTitle></CardHeader>
              <CardContent>
                <Table>
                  <TableHeader><TableRow>
                    <TableHead>Time</TableHead><TableHead>Service</TableHead><TableHead>Model</TableHead>
                    <TableHead>Tokens In</TableHead><TableHead>Tokens Out</TableHead>
                    <TableHead>Cache Read</TableHead><TableHead>Cost</TableHead><TableHead>Latency</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>
                    {costLog?.items?.map((r: any) => (
                      <TableRow key={r.id}>
                        <TableCell className="text-xs text-muted-foreground">{new Date(r.created_at).toLocaleTimeString()}</TableCell>
                        <TableCell>{r.service}</TableCell>
                        <TableCell className="font-mono text-xs">{r.model}</TableCell>
                        <TableCell>{r.input_tokens.toLocaleString()}</TableCell>
                        <TableCell>{r.output_tokens.toLocaleString()}</TableCell>
                        <TableCell>{r.cache_read_tokens > 0 ? <Badge variant="secondary">{r.cache_read_tokens.toLocaleString()}</Badge> : "—"}</TableCell>
                        <TableCell>${Number(r.cost_usd).toFixed(5)}</TableCell>
                        <TableCell>{r.latency_ms ? `${r.latency_ms}ms` : "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Users tab */}
          <TabsContent value="users">
            <Card>
              <CardContent className="pt-4">
                <Table>
                  <TableHeader><TableRow>
                    <TableHead>Email</TableHead><TableHead>Name</TableHead><TableHead>Hospital</TableHead>
                    <TableHead>Role</TableHead><TableHead>Admin</TableHead><TableHead>Joined</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>
                    {users?.map((u: any) => (
                      <TableRow key={u.id}>
                        <TableCell className="text-xs">{u.email}</TableCell>
                        <TableCell>{u.name}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{u.hospital_name}</TableCell>
                        <TableCell><Badge variant="outline">{u.role}</Badge></TableCell>
                        <TableCell>{u.is_admin ? <Badge>Admin</Badge> : "—"}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{new Date(u.created_at).toLocaleDateString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* API Keys tab */}
          <TabsContent value="apikeys">
            <Card>
              <CardContent className="pt-4 space-y-3">
                {apiKeys && Object.entries(apiKeys).map(([key, val]: [string, any]) => (
                  <div key={key} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div>
                      <div className="font-medium capitalize">{key.replace(/_/g, " ")}</div>
                      <div className="text-xs text-muted-foreground font-mono">{val.masked}</div>
                    </div>
                    <Badge variant={val.configured ? "default" : "destructive"}>
                      {val.configured ? "Configured" : "Missing"}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Benchmark tab */}
          <TabsContent value="benchmark" className="space-y-4">
            <Card>
              <CardHeader><CardTitle className="text-sm">GPT-4.1 vs Claude Sonnet 4.6</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex gap-2">
                  <Input
                    placeholder="Document ID..."
                    value={benchmarkDocId}
                    onChange={e => setBenchmarkDocId(e.target.value)}
                  />
                  <Button onClick={runBenchmark} disabled={benchmarking}>
                    {benchmarking ? "Running..." : "Run Benchmark"}
                  </Button>
                </div>
                {benchmarkResult && (
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    {["gpt_4_1", "claude_sonnet_4_6"].map(key => {
                      const r = benchmarkResult[key];
                      return (
                        <Card key={key}>
                          <CardHeader><CardTitle className="text-sm font-mono">{key.replace(/_/g, "-")}</CardTitle></CardHeader>
                          <CardContent className="space-y-2 text-sm">
                            <div className="flex justify-between"><span className="text-muted-foreground">Cost</span><span className="font-bold">${Number(r.cost_usd).toFixed(5)}</span></div>
                            <div className="flex justify-between"><span className="text-muted-foreground">Latency</span><span>{r.latency_ms}ms</span></div>
                            <div className="flex justify-between"><span className="text-muted-foreground">Input tokens</span><span>{r.input_tokens?.toLocaleString()}</span></div>
                            <div className="flex justify-between"><span className="text-muted-foreground">Output tokens</span><span>{r.output_tokens?.toLocaleString()}</span></div>
                            {r.cache_read_tokens > 0 && <div className="flex justify-between"><span className="text-muted-foreground">Cache read</span><Badge variant="secondary">{r.cache_read_tokens}</Badge></div>}
                            <div className="border-t pt-2">
                              <div className="text-muted-foreground text-xs mb-1">Underpayment found</div>
                              <div>{r.result?.has_underpayment ? <Badge>Yes — ${r.result.underpayment_amount}</Badge> : <Badge variant="outline">No</Badge>}</div>
                              <div className="text-xs text-muted-foreground mt-1">{r.result?.reasoning?.slice(0, 200)}...</div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
