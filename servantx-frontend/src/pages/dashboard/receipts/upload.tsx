import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { BillingRecordBulkUpload } from "@/components/receipts/ReceiptBulkUpload";
import { BillingRecord835Upload } from "@/components/receipts/Receipt835Upload";
import { BillingRecordZipUpload } from "@/components/receipts/ReceiptZipUpload";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function BillingRecordUploadPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Upload Billing Records</h1>
          <p className="text-muted-foreground">
            Upload one or more billing record files, or a ZIP file containing multiple billing records. Rule scan starts automatically after upload.
          </p>
        </div>

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
            <BillingRecord835Upload />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
