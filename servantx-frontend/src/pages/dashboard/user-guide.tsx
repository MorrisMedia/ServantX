import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, FileCheck, Users, Bot } from "lucide-react";

export default function UserGuidePage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Operations Guide</h1>
          <p className="text-muted-foreground">
            Product scope, HIPAA-safe operating rules, and background-agent constraints for admin and analyst teams.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Users className="h-5 w-5" /> Access model</CardTitle>
              <CardDescription>Current target operating model</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <p><strong className="text-foreground">Admin</strong>: tenant setup, contracts, source-of-truth files, batch oversight, report approval.</p>
              <p><strong className="text-foreground">Analyst</strong>: audit review, evidence validation, packet drafting, escalation notes.</p>
              <p>Client/patient-facing access is not the target for this version of the product.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><FileCheck className="h-5 w-5" /> Audit workflow</CardTitle>
              <CardDescription>What the system is designed to do</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <p>1. Upload billing exports by client and batch.</p>
              <p>2. Normalize records and apply contract/public-rate logic.</p>
              <p>3. Flag only defensible underpayments with source citations.</p>
              <p>4. Present findings in visual reports and analyst queues.</p>
              <p>5. Draft appeal support materials for human approval.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Shield className="h-5 w-5" /> HIPAA-safe AI rules</CardTitle>
              <CardDescription>Non-negotiable controls</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <p>No raw PHI goes to external LLMs.</p>
              <p>AI can only use tokenized, hashed, aggregated, or de-identified data.</p>
              <p>Dollar findings must come from deterministic rules and auditable source-of-truth logic.</p>
              <p>Outbound letters and summaries require human review before release.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Bot className="h-5 w-5" /> Background agent guardrails</CardTitle>
              <CardDescription>What autonomous helpers may and may not do</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <p><strong className="text-foreground">Allowed:</strong> monitor queues, summarize counts, flag stalled batches, prepare admin alerts.</p>
              <p><strong className="text-foreground">Not allowed:</strong> make reimbursement decisions, export PHI, submit appeals, or invent rationales.</p>
              <p>Every agent action should be logged, reversible where possible, and visible to admins.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
