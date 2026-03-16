import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { BillingRecordBulkUpload } from "@/components/receipts/ReceiptBulkUpload";
import { BillingRecord835Upload } from "@/components/receipts/Receipt835Upload";
import { BillingRecordZipUpload } from "@/components/receipts/ReceiptZipUpload";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getActiveProjectId, setActiveProjectId } from "@/lib/activeProject";
import { listProjects } from "@/lib/api/projects";
import { useQuery } from "@tanstack/react-query";

export default function BillingRecordUploadPage() {
  const projectsQuery = useQuery({ queryKey: ["/projects"], queryFn: listProjects });
  const search = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();
  const queryProjectId = search.get('projectId');
  const activeProjectId = queryProjectId || getActiveProjectId();
  if (queryProjectId) setActiveProjectId(queryProjectId);
  const activeProject = projectsQuery.data?.find((project) => project.id === activeProjectId) || null;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Upload Billing Records</h1>
          <p className="text-muted-foreground">
            Upload one or more billing record files, or a ZIP file containing multiple billing records. Rule scan starts automatically after upload.
          </p>
        </div>

        <Card>
          <CardHeader><CardTitle>Active Client Workspace</CardTitle></CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {activeProject ? `${activeProject.name} (${activeProject.slug})` : 'No client selected yet. Go back to Clients and set one active first.'}
          </CardContent>
        </Card>

        <Tabs defaultValue="upload" className="space-y-6">
          <TabsList>
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="zip">ZIP Upload</TabsTrigger>
            <TabsTrigger value="era835">835 ERA</TabsTrigger>
          </TabsList>

          <TabsContent value="upload">
            <BillingRecordBulkUpload />
          </TabsContent>

          <TabsContent value="zip">
            <BillingRecordZipUpload />
          </TabsContent>

          <TabsContent value="era835">
            <BillingRecord835Upload projectId={activeProjectId || undefined} projectName={activeProject?.name} />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
