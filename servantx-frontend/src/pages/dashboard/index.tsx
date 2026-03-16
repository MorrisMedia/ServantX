import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createProject, ensureDefaultProject, listProjects } from "@/lib/api/projects";
import { getActiveProjectId, setActiveProjectId } from "@/lib/activeProject";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, FolderOpen, PlusCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Link } from "wouter";

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [clientName, setClientName] = useState("");
  const [activeProjectId, setActiveProjectIdState] = useState<string | null>(getActiveProjectId());

  const projectsQuery = useQuery({
    queryKey: ["/projects"],
    queryFn: listProjects,
  });

  const ensureDefaultMutation = useMutation({
    mutationFn: ensureDefaultProject,
    onSuccess: (project) => {
      setActiveProjectId(project.id);
      setActiveProjectIdState(project.id);
      queryClient.invalidateQueries({ queryKey: ["/projects"] });
    },
  });

  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      toast.success(`Client workspace created: ${project.name}`);
      setActiveProjectId(project.id);
      setActiveProjectIdState(project.id);
      setClientName("");
      queryClient.invalidateQueries({ queryKey: ["/projects"] });
    },
    onError: (err: Error) => toast.error(err.message || "Failed to create client workspace"),
  });

  useEffect(() => {
    if (!projectsQuery.isSuccess) return;
    if (projectsQuery.data.length === 0 && !ensureDefaultMutation.isPending) {
      ensureDefaultMutation.mutate();
      return;
    }
    if (!activeProjectId && projectsQuery.data.length > 0) {
      setActiveProjectId(projectsQuery.data[0].id);
      setActiveProjectIdState(projectsQuery.data[0].id);
    }
  }, [projectsQuery.isSuccess, projectsQuery.data, activeProjectId]);

  const activeProject = useMemo(
    () => projectsQuery.data?.find((project) => project.id === activeProjectId) || null,
    [projectsQuery.data, activeProjectId]
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Clients</h1>
          <p className="text-muted-foreground">Select a client workspace first. Uploads, documents, and reporting should then happen inside that client context.</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Create Client Workspace</CardTitle>
            <CardDescription>Spin up a dedicated workspace for a client before uploading records or contracts.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 md:flex-row">
            <Input value={clientName} onChange={(e) => setClientName(e.target.value)} placeholder="e.g. Austin Cardiology Associates" />
            <Button onClick={() => createProjectMutation.mutate({ name: clientName.trim() })} disabled={!clientName.trim() || createProjectMutation.isPending}>
              <PlusCircle className="mr-2 h-4 w-4" />
              Create Client
            </Button>
          </CardContent>
        </Card>

        {activeProject && (
          <Card className="border-primary/40 bg-primary/5">
            <CardHeader>
              <CardTitle>Active Client</CardTitle>
              <CardDescription>This is the current client workspace the analyst should work inside.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="text-lg font-semibold">{activeProject.name}</div>
                <div className="text-sm text-muted-foreground">Slug: {activeProject.slug} · Status: {activeProject.status}</div>
              </div>
              <div className="flex gap-2">
                <Link href={`/dashboard/receipts/upload?projectId=${activeProject.id}`}><Button>Upload Into Client</Button></Link>
                <Link href={`/dashboard/documents?projectId=${activeProject.id}`}><Button variant="outline">View Client Documents</Button></Link>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(projectsQuery.data || []).map((project) => (
            <Card key={project.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Building2 className="h-4 w-4" />{project.name}</CardTitle>
                <CardDescription>{project.description || "Client workspace"}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm text-muted-foreground">{project.slug}</div>
                <div className="flex flex-wrap gap-2">
                  <Button variant={project.id === activeProjectId ? "default" : "outline"} size="sm" onClick={() => { setActiveProjectId(project.id); setActiveProjectIdState(project.id); toast.success(`${project.name} is now active`); }}>
                    <FolderOpen className="mr-2 h-4 w-4" />
                    {project.id === activeProjectId ? "Active" : "Set Active"}
                  </Button>
                  <Link href={`/dashboard/receipts/upload?projectId=${project.id}`}><Button size="sm" variant="ghost">Upload</Button></Link>
                  <Link href={`/dashboard/documents?projectId=${project.id}`}><Button size="sm" variant="ghost">Documents</Button></Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
