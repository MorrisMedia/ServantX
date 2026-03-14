import { useRoute } from "wouter";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { DocumentDetail } from "@/components/documents/DocumentDetail";

export default function DocumentDetailPage() {
  const [, params] = useRoute("/dashboard/documents/:id");
  const documentId = params?.id || "";

  if (!documentId) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <p className="text-destructive">Document ID is required</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <DocumentDetail documentId={documentId} />
    </DashboardLayout>
  );
}



