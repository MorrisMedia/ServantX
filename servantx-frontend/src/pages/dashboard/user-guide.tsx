import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  DollarSign,
  FileText,
  HelpCircle,
  Info,
  Layers,
  Lock,
  RefreshCw,
  Settings,
  Shield,
  Upload,
  Zap,
} from "lucide-react";

// ─── Helper components ────────────────────────────────────────────────────────

function SectionAnchor({ id }: { id: string }) {
  return <span id={id} className="block -mt-16 pt-16 invisible" aria-hidden />;
}

function StepList({ steps }: { steps: { title: string; body: React.ReactNode }[] }) {
  return (
    <ol className="space-y-4">
      {steps.map((step, i) => (
        <li key={i} className="flex gap-4">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold mt-0.5">
            {i + 1}
          </div>
          <div className="space-y-1">
            <p className="font-semibold text-sm">{step.title}</p>
            <div className="text-sm text-muted-foreground leading-relaxed">{step.body}</div>
          </div>
        </li>
      ))}
    </ol>
  );
}

function ScreenshotCallout({ description }: { description: string }) {
  return (
    <div className="my-4 flex items-start gap-3 rounded-lg border border-dashed border-muted-foreground/40 bg-muted/30 px-4 py-3">
      <Info className="h-4 w-4 shrink-0 text-muted-foreground mt-0.5" />
      <p className="text-xs text-muted-foreground italic">[Screenshot: {description}]</p>
    </div>
  );
}

function Callout({
  variant = "info",
  children,
}: {
  variant?: "info" | "warning" | "success" | "tip";
  children: React.ReactNode;
}) {
  const styles = {
    info: "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950/30 dark:border-blue-800 dark:text-blue-300",
    warning: "bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950/30 dark:border-amber-800 dark:text-amber-300",
    success: "bg-green-50 border-green-200 text-green-800 dark:bg-green-950/30 dark:border-green-800 dark:text-green-300",
    tip: "bg-purple-50 border-purple-200 text-purple-800 dark:bg-purple-950/30 dark:border-purple-800 dark:text-purple-300",
  };
  const icons = {
    info: <Info className="h-4 w-4 shrink-0 mt-0.5" />,
    warning: <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />,
    success: <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />,
    tip: <Zap className="h-4 w-4 shrink-0 mt-0.5" />,
  };
  return (
    <div className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm my-3 ${styles[variant]}`}>
      {icons[variant]}
      <div className="leading-relaxed">{children}</div>
    </div>
  );
}

function SectionHeader({
  icon: Icon,
  title,
  subtitle,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="flex items-start gap-3 mb-5">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
        <Icon className="h-5 w-5 text-primary" />
      </div>
      <div>
        <h2 className="text-xl font-bold tracking-tight">{title}</h2>
        {subtitle && <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

// ─── Table of Contents ────────────────────────────────────────────────────────

const TOC_ITEMS = [
  { id: "quick-start", label: "Quick Start (5 Steps)" },
  { id: "accounts", label: "Accounts & Login" },
  { id: "client-workspaces", label: "Client Workspaces" },
  { id: "uploading-835s", label: "Uploading 835 Files" },
  { id: "pricing-modes", label: "Pricing Modes Explained" },
  { id: "documents", label: "Reviewing Audit Documents" },
  { id: "contracts", label: "Contracts" },
  { id: "appeal-workflow", label: "Appeal Workflow" },
  { id: "roi-dashboard", label: "ROI Dashboard" },
  { id: "settings", label: "Settings" },
  { id: "hipaa", label: "HIPAA Safeguards" },
  { id: "faq", label: "FAQ & Troubleshooting" },
];

// ─── Main component ───────────────────────────────────────────────────────────

export default function UserGuidePage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl space-y-10">

        {/* Page header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <BookOpen className="h-7 w-7 text-primary" />
            ServantX User Guide
          </h1>
          <p className="text-muted-foreground mt-1">
            Complete guide for billing managers — from first upload to recovered payment.
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge variant="secondary">v2026</Badge>
            <Badge variant="outline">HIPAA Compliant</Badge>
            <Badge variant="outline">For Billing Teams</Badge>
          </div>
        </div>

        {/* Table of Contents */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">On This Page</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="grid gap-1 sm:grid-cols-2">
              {TOC_ITEMS.map((item) => (
                <li key={item.id}>
                  <a
                    href={`#${item.id}`}
                    className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors py-0.5"
                  >
                    <ChevronRight className="h-3.5 w-3.5 text-primary shrink-0" />
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Separator />

        {/* ─── QUICK START ─── */}
        <section>
          <SectionAnchor id="quick-start" />
          <SectionHeader
            icon={Zap}
            title="Quick Start — 5 Steps to Your First Result"
            subtitle="New to ServantX? Follow these steps to see your first underpayment audit in under 10 minutes."
          />

          <Callout variant="tip">
            You need at least one 835 remittance file from your clearinghouse or payer portal before you begin. If you don't have one yet, ask your billing system administrator to export a recent batch.
          </Callout>

          <div className="mt-4">
            <StepList
              steps={[
                {
                  title: "Register and log in",
                  body: (
                    <>
                      Go to <strong>www.servantx.ai</strong>, click <strong>Register</strong>, and create your account with your hospital email address. After registering, check your inbox for a confirmation email, then log in.
                    </>
                  ),
                },
                {
                  title: "Create a client workspace",
                  body: (
                    <>
                      On the <strong>Clients</strong> dashboard, type your hospital or department name in the <em>Create Client Workspace</em> field and click <strong>Create Client</strong>. This workspace keeps all files, documents, and appeals organized together.
                    </>
                  ),
                },
                {
                  title: "Upload a contract (optional but recommended)",
                  body: (
                    <>
                      Navigate to <strong>Contracts</strong> in the left menu. Upload a PDF or Word document of your payer contract. ServantX will automatically read the reimbursement terms so it can compare actual payments against your agreed rates. You can skip this step and use Medicare rates only, but contract-based auditing catches more underpayments.
                    </>
                  ),
                },
                {
                  title: "Upload your 835 file",
                  body: (
                    <>
                      Go to <strong>Receipts → Upload</strong>. Select your .835 remittance file and click <strong>Upload</strong>. ServantX processes each claim — repricing it, comparing it to the fee schedule, and flagging any underpayments.
                    </>
                  ),
                },
                {
                  title: "Review findings and generate an appeal",
                  body: (
                    <>
                      Navigate to <strong>Documents</strong>. Click any flagged claim to see the full pricing breakdown. If you agree with the finding, click <strong>Generate Appeal Letter</strong> to create a ready-to-file appeal letter in one click.
                    </>
                  ),
                },
              ]}
            />
          </div>

          <ScreenshotCallout description="Quick Start flow — five-step visual walkthrough from upload to first appeal letter" />
        </section>

        <Separator />

        {/* ─── ACCOUNTS & LOGIN ─── */}
        <section>
          <SectionAnchor id="accounts" />
          <SectionHeader
            icon={Lock}
            title="Accounts & Login"
            subtitle="Managing your credentials and access."
          />

          <Accordion type="multiple" className="border rounded-lg divide-y overflow-hidden">
            <AccordionItem value="register" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Creating an account</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Visit <strong>www.servantx.ai</strong> and click <strong>Register</strong>. Fill in your name, hospital email, and a strong password. Use your work email — it will be associated with your hospital's billing records.
                </p>
                <Callout variant="info">
                  If your hospital uses Single Sign-On (SSO) through a network login, contact your IT administrator — they may need to provision your account.
                </Callout>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="login" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Logging in</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Go to <strong>www.servantx.ai</strong> and enter your email and password. Click <strong>Sign In</strong>. You will land on the Clients dashboard.
                </p>
                <p>
                  Sessions expire after a period of inactivity. If you are redirected to the login page mid-session, your session timed out — simply log back in. Your data is never lost.
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="forgot-password" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Forgot or reset your password</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>On the login page, click <strong>Forgot password?</strong></p>
                <StepList
                  steps={[
                    { title: "Enter your email address", body: "Type the email you registered with and click Send Reset Link." },
                    { title: "Check your inbox", body: "You will receive an email with a one-time reset link. It expires in 30 minutes." },
                    { title: "Set a new password", body: "Click the link in the email, enter your new password twice, and click Reset Password." },
                  ]}
                />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="change-password" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Changing your password while logged in</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Go to <strong>Settings → Password</strong> in the left navigation. Enter your current password, then your new password twice. Click <strong>Update Password</strong>.
                </p>
                <Callout variant="warning">
                  Choose a password that is at least 12 characters long. Do not share your password with colleagues — each team member should have their own account.
                </Callout>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </section>

        <Separator />

        {/* ─── CLIENT WORKSPACES ─── */}
        <section>
          <SectionAnchor id="client-workspaces" />
          <SectionHeader
            icon={Layers}
            title="Client Workspaces"
            subtitle="Organize files, audits, and appeals by hospital or department."
          />

          <div className="text-sm text-muted-foreground space-y-3 mb-5">
            <p>
              Every upload, document, contract, and appeal lives inside a <strong>Client Workspace</strong>. If your billing team manages multiple hospitals or departments, create a separate workspace for each. This keeps audits cleanly separated so reporting and appeal tracking don't mix across entities.
            </p>
          </div>

          <Card className="mb-4">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Creating a workspace</CardTitle>
            </CardHeader>
            <CardContent>
              <StepList
                steps={[
                  { title: "Open the Clients page", body: "Click Clients in the left navigation menu." },
                  {
                    title: "Enter the client name",
                    body: "Type the name of the hospital, practice, or department into the Create Client Workspace field. Example: \"Austin Cardiology Associates\" or \"River Oaks Hospital — Outpatient\".",
                  },
                  { title: "Click Create Client", body: "The workspace appears immediately in your client list and becomes the active workspace." },
                ]}
              />
            </CardContent>
          </Card>

          <Card className="mb-4">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Switching between workspaces</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <p>
                On the Clients page, find the workspace you want to switch to and click <strong>Set Active</strong>. The active workspace is highlighted with a colored border and shows an <em>Active</em> badge. All subsequent uploads and documents will belong to that client until you switch again.
              </p>
              <Callout variant="tip">
                Before uploading a new batch of 835 files, always confirm the correct client workspace is active. Look for the "Active Client" card near the top of the Clients page.
              </Callout>
            </CardContent>
          </Card>

          <ScreenshotCallout description="Clients page showing two workspaces, one highlighted as Active with Set Active button on the other" />
        </section>

        <Separator />

        {/* ─── UPLOADING 835s ─── */}
        <section>
          <SectionAnchor id="uploading-835s" />
          <SectionHeader
            icon={Upload}
            title="Uploading 835 Remittance Files"
            subtitle="How to get your payment data into ServantX for auditing."
          />

          <div className="text-sm text-muted-foreground space-y-2 mb-5">
            <p>
              An <strong>835 file</strong> is an electronic remittance advice (ERA) — the standardized file your insurance payers send to explain what they paid and why. Your clearinghouse (e.g., Availity, Change Healthcare, Waystar) or your practice management system can export these files.
            </p>
            <p>
              ServantX accepts <strong>.835 files</strong> individually, in bulk, or packaged in a <strong>ZIP archive</strong>. There is no limit on how many files you can upload — large batches are automatically split into smaller processing groups.
            </p>
          </div>

          <Accordion type="multiple" className="border rounded-lg divide-y overflow-hidden">
            <AccordionItem value="single" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Upload a single 835 file</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-3 pb-4">
                <StepList
                  steps={[
                    { title: "Confirm active client", body: "Make sure the correct client workspace is active (see Client Workspaces section)." },
                    { title: "Navigate to Receipts → Upload", body: "Click Receipts in the left menu, then select Upload." },
                    { title: "Select your file", body: "Click Choose File and select your .835 file from your computer." },
                    { title: "Click Upload", body: "ServantX validates the file format, assigns a unique fingerprint, and begins processing. You will see a confirmation message when the upload succeeds." },
                    { title: "Wait for processing", body: "Processing time depends on the number of claims. A file with 50 claims typically completes in under two minutes. Refresh the Documents page to see results as they become available." },
                  ]}
                />
                <Callout variant="info">
                  ServantX automatically detects duplicate uploads using a file fingerprint (SHA-256 hash). If you accidentally upload the same file twice, the second upload is rejected with a message explaining the file already exists. This prevents duplicate audit records.
                </Callout>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="bulk" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Upload multiple files at once (Bulk Upload)</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-3 pb-4">
                <p>
                  Navigate to <strong>Receipts → Bulk Upload</strong>. Select multiple .835 files at once using your file browser (hold Ctrl or Cmd to select multiple files). Click <strong>Upload All</strong>. Each file is processed independently — if one file has an error, the others continue uninterrupted.
                </p>
                <ScreenshotCallout description="Bulk Upload page with multiple files selected showing file names and sizes in a list" />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="zip" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Upload a ZIP archive of 835 files</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-3 pb-4">
                <p>
                  If your clearinghouse delivers a compressed archive, you can upload the ZIP directly. Navigate to <strong>Receipts → Upload ZIP</strong> and select the .zip file. ServantX extracts and processes all .835 files inside automatically.
                </p>
                <Callout variant="tip">
                  ZIP upload is the fastest way to load a full month of remittance files. If your clearinghouse delivers files in a nightly batch, download the ZIP for the period you want to audit and upload it in one step.
                </Callout>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="large-files" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Large files with many claims</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  ServantX processes up to 30 claims per batch run. If your 835 file contains more than 30 claims, the system automatically splits it into smaller chunks and processes them in sequence. You do not need to do anything special — processing just takes longer. A file with 300 claims may take 10–15 minutes to fully process.
                </p>
                <p>
                  Results appear in Documents as each batch completes, so you may see some claims while others are still being processed.
                </p>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </section>

        <Separator />

        {/* ─── PRICING MODES ─── */}
        <section>
          <SectionAnchor id="pricing-modes" />
          <SectionHeader
            icon={DollarSign}
            title="Pricing Modes Explained"
            subtitle="How ServantX determines what a claim should have been paid."
          />

          <div className="text-sm text-muted-foreground space-y-2 mb-5">
            <p>
              ServantX uses one of four <strong>Pricing Engines</strong> to reprice each claim: Medicare fee schedules published by CMS, state Medicaid rates, contract rules extracted from your uploaded payer contracts, or a combination of all three. The <strong>Pricing Mode</strong> setting in your hospital profile controls which engine is used.
            </p>
          </div>

          <Card className="mb-6">
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-32">Mode</TableHead>
                    <TableHead>What It Does</TableHead>
                    <TableHead className="w-40">Best For</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>
                      <Badge variant="default">AUTO</Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      Reads the payer listed in the 835 file and picks the right engine automatically. Medicare payers use Medicare fee schedules; Medicaid payers use state Medicaid rates; commercial payers use your uploaded contract plus AI analysis.
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">Most hospitals — handles mixed payer batches</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Badge variant="secondary">MEDICARE</Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      Forces all claims through CMS 2026 Medicare fee schedules (MPFS for professional claims, IPPS for inpatient, OPPS/APC for outpatient) regardless of who the payer is.
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">Medicare-only audits or benchmarking commercial rates against Medicare</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Badge variant="secondary">MEDICAID</Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      Forces all claims through the Texas Medicaid Fee-for-Service schedule. Claims from states other than Texas fall back to Contract + AI analysis.
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">Texas Medicaid managed care audits</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Badge variant="secondary">CONTRACT</Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      Uses only the rules extracted from your uploaded payer contracts, supplemented by AI analysis. No fee schedules are applied.
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">Hospitals with strong contract coverage and complex carve-outs</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Badge variant="outline">ALL</Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      Runs every available engine on every claim and selects the result that shows the highest underpayment with at least 30% confidence. Most aggressive audit mode.
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">Maximum recovery scenarios; QA and benchmarking</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h3 className="font-semibold text-sm">The Three Fee Schedule Engines</h3>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                {
                  title: "MPFS",
                  subtitle: "Medicare Physician Fee Schedule",
                  body: "Used for professional/physician claims. Covers office visits, procedures, and specialist services billed on a CMS-1500 form.",
                },
                {
                  title: "IPPS",
                  subtitle: "Inpatient Prospective Payment",
                  body: "Used for hospital inpatient admissions billed on a UB-04 form with DRG codes. Covers acute care stays, surgery, and inpatient procedures.",
                },
                {
                  title: "OPPS / APC",
                  subtitle: "Outpatient Prospective Payment",
                  body: "Used for hospital outpatient services billed by Ambulatory Payment Classification codes — ER visits, same-day surgery, infusion, imaging.",
                },
              ].map((engine) => (
                <Card key={engine.title} className="border-l-4 border-l-primary/60">
                  <CardContent className="p-4 space-y-1">
                    <p className="font-bold text-sm">{engine.title}</p>
                    <p className="text-xs text-muted-foreground font-medium">{engine.subtitle}</p>
                    <p className="text-xs text-muted-foreground leading-relaxed">{engine.body}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <Callout variant="tip" >
            Not sure which mode to use? Start with <strong>AUTO</strong>. It is the default and handles mixed payer batches correctly. You can always re-run an audit with a different mode later by changing the setting in <strong>Settings → Pricing Config</strong>.
          </Callout>
        </section>

        <Separator />

        {/* ─── DOCUMENTS ─── */}
        <section>
          <SectionAnchor id="documents" />
          <SectionHeader
            icon={FileText}
            title="Reviewing Audit Documents"
            subtitle="Understanding what ServantX found and how to act on it."
          />

          <div className="text-sm text-muted-foreground space-y-2 mb-5">
            <p>
              After an 835 file is processed, every claim becomes an <strong>Audit Document</strong>. Documents live under the <strong>Documents</strong> section in the left menu. Each document shows the original payment, the repriced expected amount, the variance, and the AI's reasoning.
            </p>
          </div>

          <Accordion type="multiple" className="border rounded-lg divide-y overflow-hidden">
            <AccordionItem value="list-view" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">The Documents list</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-3 pb-4">
                <p>
                  The Documents page shows all processed claims for the active client workspace. Each row displays the claim reference number, payer name, amount paid, repriced amount, underpayment variance, and current appeal status.
                </p>
                <p>
                  Use the <strong>status filter</strong> at the top to narrow the list — for example, filter to <em>Identified</em> to see only claims with a confirmed underpayment that have not yet been appealed.
                </p>
                <ScreenshotCallout description="Documents list with status filter dropdown open showing appeal status options" />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="claim-detail" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Understanding the claim detail page</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-3 pb-4">
                <p>Click any claim row to open its detail page. You will see:</p>
                <ul className="space-y-2 ml-4 list-disc">
                  <li>
                    <strong>Claim summary</strong> — payer, service date, procedure codes, amount billed, amount paid, expected amount, and variance.
                  </li>
                  <li>
                    <strong>Multi-engine comparison table</strong> — a side-by-side view of what each pricing engine calculated, with confidence bars showing how certain each result is. Higher confidence means more evidence supports that price.
                  </li>
                  <li>
                    <strong>AI Reasoning</strong> (collapsible) — a plain-English explanation of why the AI flagged this claim as an underpayment. This section cites the specific fee schedule line or contract clause used.
                  </li>
                  <li>
                    <strong>Appeal status</strong> — current stage of the appeal for this claim.
                  </li>
                </ul>
                <ScreenshotCallout description="Claim detail page showing summary bar, multi-engine comparison table with confidence bars, and collapsed AI Reasoning section" />
                <Callout variant="info">
                  The <strong>confidence bar</strong> reflects how many independent data sources agree on the expected reimbursement. A claim with 80%+ confidence from the Medicare MPFS engine is a strong candidate for appeal. A claim at 30–50% confidence may need additional review before filing.
                </Callout>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="csv-export" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Exporting audit findings to CSV</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  On the Documents list page, click <strong>Export CSV</strong>. The downloaded file contains one row per claim with all pricing details, variance amounts, confidence scores, and appeal statuses. Use this file for external reporting, payer meetings, or to share with your compliance team.
                </p>
                <Callout variant="warning">
                  The CSV export contains claim-level financial data. Store it on a secured, access-controlled drive consistent with your hospital's PHI handling policies.
                </Callout>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </section>

        <Separator />

        {/* ─── CONTRACTS ─── */}
        <section>
          <SectionAnchor id="contracts" />
          <SectionHeader
            icon={FileText}
            title="Contracts"
            subtitle="Upload payer contracts so ServantX can reprice claims against your negotiated rates."
          />

          <div className="text-sm text-muted-foreground space-y-2 mb-5">
            <p>
              When you upload a payer contract, ServantX uses AI to extract the fee schedule entries, percentage-of-billed-charges rules, carve-outs, and other reimbursement terms. These rules are stored in your contract's <strong>rule library</strong> and automatically applied when repricing matching claims.
            </p>
          </div>

          <Accordion type="multiple" className="border rounded-lg divide-y overflow-hidden">
            <AccordionItem value="upload-contract" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Uploading a contract</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-3 pb-4">
                <StepList
                  steps={[
                    { title: "Navigate to Contracts", body: "Click Contracts in the left navigation menu." },
                    { title: "Click Upload Contract", body: "Select a PDF or Word (.docx) file from your computer. ServantX accepts contracts up to 50 MB." },
                    { title: "Wait for extraction", body: "The AI reads your contract and builds a rule library. This typically takes 30–90 seconds depending on contract length. You will see a processing indicator." },
                    {
                      title: "Review the extracted rules",
                      body: "Once extraction is complete, click the contract to see the rules that were found — fee schedule amounts, percentage rules, and special terms. Review these for accuracy.",
                    },
                  ]}
                />
                <Callout variant="info">
                  Contracts are associated with the active client workspace. Upload one contract per payer per workspace. If you have separate contracts for professional vs. facility services, upload them as separate documents.
                </Callout>
                <ScreenshotCallout description="Contracts page showing uploaded contract with status 'Extracted' and rule count badge" />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="chat-contract" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Asking questions about a contract</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Open any uploaded contract and use the <strong>Chat</strong> panel to ask questions in plain English. Examples:
                </p>
                <ul className="ml-4 list-disc space-y-1">
                  <li>"What is the reimbursement rate for CPT 99213?"</li>
                  <li>"Does this contract have a carve-out for implants?"</li>
                  <li>"What is the timely filing deadline for appeals?"</li>
                  <li>"What percentage of Medicare does this payer pay for outpatient surgery?"</li>
                </ul>
                <p>
                  ServantX answers using only the text of your contract — it will not invent terms that aren't there. If a term isn't found, it will tell you.
                </p>
                <ScreenshotCallout description="Contract chat panel showing a question about CPT 99213 and an answer citing the specific contract clause" />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="reprocess-contract" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Re-extracting contract rules</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  If you notice that ServantX missed rules during the initial extraction — for example, an addendum was not captured — click <strong>Reprocess Contract</strong> on the contract detail page. The AI will re-read the entire document and rebuild the rule library. Previous repricing results for this client are not automatically updated; re-run affected 835 uploads if needed.
                </p>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </section>

        <Separator />

        {/* ─── APPEAL WORKFLOW ─── */}
        <section>
          <SectionAnchor id="appeal-workflow" />
          <SectionHeader
            icon={ArrowRight}
            title="Appeal Workflow"
            subtitle="From identified underpayment to recovered payment — the full lifecycle."
          />

          <div className="text-sm text-muted-foreground space-y-2 mb-5">
            <p>
              Every flagged claim moves through a defined appeal lifecycle. ServantX tracks the status of each appeal so you always know what stage a claim is in and what action is needed next.
            </p>
          </div>

          {/* Status flow */}
          <Card className="mb-6">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Appeal Status Flow</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap items-center gap-2 text-sm">
                {[
                  { label: "None", color: "bg-muted text-muted-foreground" },
                  { label: "→", color: "" },
                  { label: "Identified", color: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" },
                  { label: "→", color: "" },
                  { label: "Drafted", color: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300" },
                  { label: "→", color: "" },
                  { label: "Filed", color: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300" },
                  { label: "→", color: "" },
                  { label: "Under Review", color: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300" },
                  { label: "→", color: "" },
                  { label: "Approved", color: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" },
                ].map((item, i) =>
                  item.label === "→" ? (
                    <span key={i} className="text-muted-foreground">→</span>
                  ) : (
                    <span key={i} className={`px-2 py-1 rounded text-xs font-semibold ${item.color}`}>{item.label}</span>
                  )
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-3">
                Appeals can also resolve as <span className="font-semibold">Partial</span> (some recovery) or <span className="font-semibold">Denied</span>. Both outcomes are tracked for ROI reporting.
              </p>
            </CardContent>
          </Card>

          <div className="space-y-4">
            {[
              {
                status: "None",
                color: "border-l-muted-foreground/30",
                what: "The claim has been processed but no underpayment was found, or the finding has not yet been reviewed.",
                action: "No action required. If you believe a claim was underpaid despite no flag, check the Pricing Mode in Settings — you may need to switch to CONTRACT mode if this payer has a custom contract.",
              },
              {
                status: "Identified",
                color: "border-l-blue-500",
                what: "ServantX found a probable underpayment and is confident enough to flag it for review.",
                action: "Open the claim detail page and review the AI reasoning and pricing comparison. If you agree with the finding, proceed to generate an appeal letter.",
              },
              {
                status: "Drafted",
                color: "border-l-purple-500",
                what: "An appeal letter has been generated but not yet submitted to the payer.",
                action: "Review the letter text (click Copy or Download). Make any edits needed in your word processor, then submit through your payer's portal or by fax/mail. After submitting, update the status to Filed.",
              },
              {
                status: "Filed",
                color: "border-l-amber-500",
                what: "You have sent the appeal to the payer and are waiting for their response.",
                action: "No action required in ServantX. Update the status when you receive a response.",
              },
              {
                status: "Under Review",
                color: "border-l-orange-500",
                what: "The payer has acknowledged the appeal and is reviewing it.",
                action: "Monitor your payer portal or fax queue for a determination letter. Update status when received.",
              },
              {
                status: "Approved",
                color: "border-l-green-500",
                what: "The payer approved the appeal and agreed to pay the additional amount.",
                action: "Enter the recovered_amount when updating status to Approved so it reflects in your ROI Dashboard.",
              },
              {
                status: "Partial",
                color: "border-l-teal-500",
                what: "The payer paid part of the disputed amount.",
                action: "Enter the actual recovered amount. Consider whether a secondary appeal is warranted for the remaining balance.",
              },
              {
                status: "Denied",
                color: "border-l-red-500",
                what: "The payer rejected the appeal.",
                action: "Note the denial reason. Evaluate whether to escalate to a peer-to-peer review, external review organization, or state insurance commissioner complaint depending on the reason for denial.",
              },
            ].map((item) => (
              <Card key={item.status} className={`border-l-4 ${item.color}`}>
                <CardContent className="p-4">
                  <p className="font-semibold text-sm mb-1">{item.status}</p>
                  <p className="text-sm text-muted-foreground mb-1">{item.what}</p>
                  <p className="text-sm"><span className="font-medium">Your action: </span>{item.action}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="mt-6">
            <h3 className="font-semibold text-sm mb-3">Generating an Appeal Letter</h3>
            <StepList
              steps={[
                { title: "Open the claim detail page", body: "Navigate to Documents and click the claim you want to appeal." },
                {
                  title: "Click Generate Appeal Letter",
                  body: "ServantX automatically drafts a letter using the claim data, pricing findings, AI audit reasoning, and any relevant contract terms. The letter is created in seconds.",
                },
                {
                  title: "Review the letter",
                  body: "Read the generated letter carefully. It will reference the specific procedure codes, the amount paid, the expected amount, and the basis for the appeal (e.g., CMS 2026 MPFS rate for CPT XXXXX). Verify all figures are correct.",
                },
                {
                  title: "Copy or download",
                  body: "Click Copy to clipboard to paste into your word processor, or click Download to save as a .txt file.",
                },
                {
                  title: "Submit the appeal",
                  body: "Send the letter via the payer's official appeal submission channel — usually a web portal, fax number, or mailing address specified in your contract.",
                },
                {
                  title: "Update the status to Filed",
                  body: "Return to the claim detail page and change the appeal status to Filed. Add notes with the submission date and method if you want to track this for your records.",
                },
              ]}
            />
          </div>

          <ScreenshotCallout description="Generated appeal letter panel showing letter text, Copy and Download buttons, and status update dropdown" />

          <Callout variant="warning">
            Appeal letters generated by ServantX are drafts for human review. A billing professional should review every letter before it is submitted. Do not send letters unreviewed — payer-specific requirements may require additional language or attachments not automatically included.
          </Callout>
        </section>

        <Separator />

        {/* ─── ROI DASHBOARD ─── */}
        <section>
          <SectionAnchor id="roi-dashboard" />
          <SectionHeader
            icon={DollarSign}
            title="ROI Dashboard"
            subtitle="Track the financial impact of your audit and appeal activity."
          />

          <div className="text-sm text-muted-foreground space-y-2 mb-5">
            <p>
              Navigate to <strong>Analytics</strong> in the left menu to access the ROI Dashboard. This page updates automatically as claims are processed and appeal statuses change.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 mb-5">
            {[
              {
                title: "Total Identified",
                body: "The sum of all underpayment variance amounts across every flagged claim. This is your total potential recovery — the maximum you could recover if all appeals are approved.",
              },
              {
                title: "Total Recovered",
                body: "The actual dollars you have collected via approved appeals. This amount grows as you update appeal statuses to Approved and enter recovered amounts.",
              },
              {
                title: "Recovery Rate %",
                body: "Total Recovered divided by Total Identified. A higher percentage means your appeals are succeeding. Industry average recovery rates range from 20–60% depending on payer mix.",
              },
              {
                title: "Claims Flagged / Flag Rate %",
                body: "How many claims out of all processed claims were identified as underpaid. A flag rate above 15% may indicate a systematic underpayment issue with a specific payer.",
              },
            ].map((kpi) => (
              <Card key={kpi.title} className="border-l-4 border-l-primary/50">
                <CardContent className="p-4 space-y-1">
                  <p className="font-semibold text-sm">{kpi.title}</p>
                  <p className="text-xs text-muted-foreground leading-relaxed">{kpi.body}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="mb-4">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Appeal Pipeline Funnel</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <p>
                The funnel chart shows how many claims are at each appeal status, with a horizontal bar proportional to the count. Use this to identify bottlenecks — for example, if many claims are in <em>Drafted</em> status, your team may have appeal letters ready to file that haven't been submitted yet.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Recovery by Payer</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <p>
                The payer table ranks insurers by total underpayment identified. Use it to prioritize which payer to focus your appeal efforts on. A payer with a high identified amount and a low recovery rate is often the highest-value target.
              </p>
              <p>
                Recovery rates are color-coded: green (≥50%), yellow (20–49%), red (below 20%). Persistently red payers may indicate a contract interpretation dispute worth escalating to your managed care contracting team.
              </p>
            </CardContent>
          </Card>

          <ScreenshotCallout description="ROI Dashboard with four KPI cards at top, Appeal Pipeline funnel, and Recovery by Payer table below" />
        </section>

        <Separator />

        {/* ─── SETTINGS ─── */}
        <section>
          <SectionAnchor id="settings" />
          <SectionHeader
            icon={Settings}
            title="Settings"
            subtitle="Configure your hospital profile and audit preferences."
          />

          <Accordion type="multiple" className="border rounded-lg divide-y overflow-hidden">
            <AccordionItem value="hospital-profile" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Hospital profile</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Navigate to <strong>Settings</strong> in the left menu. The <em>Hospital</em> tab contains your organization's name and contact information. Keep this current — it appears on generated appeal letters.
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="pricing-config" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Pricing configuration</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-3 pb-4">
                <p>
                  Click the <strong>Pricing Config</strong> tab in Settings.
                </p>
                <ul className="ml-4 list-disc space-y-1">
                  <li>
                    <strong>Pricing Mode</strong> — Select AUTO, MEDICARE, MEDICAID, CONTRACT, or ALL. See the Pricing Modes section of this guide for guidance on which to choose.
                  </li>
                  <li>
                    <strong>State</strong> — Enter your hospital's two-letter state abbreviation (e.g., TX, CA). This determines which state Medicaid fee schedule is used when Medicaid repricing is triggered.
                  </li>
                </ul>
                <p>Click <strong>Save Settings</strong> to apply changes. New uploads will use the updated settings; previously processed claims are not automatically re-run.</p>
                <Callout variant="tip">
                  If you change Pricing Mode, re-upload or reprocess existing 835 files to see updated results under the new mode.
                </Callout>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="password-settings" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Changing your password</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  In Settings, scroll to the <strong>Password</strong> section. Enter your current password, then your new password twice. Click <strong>Update Password</strong>. You will receive a confirmation that the change was saved.
                </p>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </section>

        <Separator />

        {/* ─── HIPAA ─── */}
        <section>
          <SectionAnchor id="hipaa" />
          <SectionHeader
            icon={Shield}
            title="HIPAA Safeguards"
            subtitle="How ServantX protects patient information during AI processing."
          />

          <Callout variant="success">
            ServantX is designed to comply with HIPAA technical safeguard requirements. No raw Protected Health Information (PHI) is transmitted to external AI systems.
          </Callout>

          <div className="mt-4 space-y-3 text-sm text-muted-foreground">
            <Card>
              <CardContent className="p-4 space-y-2">
                <p className="font-semibold text-foreground flex items-center gap-2">
                  <Lock className="h-4 w-4 text-primary" />
                  De-identification before AI processing
                </p>
                <p>
                  Before any claim data is sent to the AI engine, ServantX automatically removes or replaces all 18 HIPAA identifiers — patient name, date of birth, member ID, address, and others. The AI model receives only tokenized, de-identified claim data: procedure codes, service dates (shifted), payment amounts, and diagnosis codes.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 space-y-2">
                <p className="font-semibold text-foreground flex items-center gap-2">
                  <Shield className="h-4 w-4 text-primary" />
                  Deterministic repricing
                </p>
                <p>
                  Dollar amounts in audit findings come from deterministic, auditable fee schedule lookups and contract rule logic — not from AI inference. The AI's role is to identify the <em>pattern</em> of underpayment and generate appeal letter language, not to invent reimbursement figures.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 space-y-2">
                <p className="font-semibold text-foreground flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                  Human approval requirement
                </p>
                <p>
                  No appeal letter or audit finding is submitted automatically. Every result requires a human reviewer to read, verify, and manually submit. ServantX generates and presents — your team approves and acts.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 space-y-2">
                <p className="font-semibold text-foreground flex items-center gap-2">
                  <Lock className="h-4 w-4 text-primary" />
                  Data handling
                </p>
                <p>
                  All data is encrypted at rest and in transit. Access is restricted to authenticated users within your organization's account. ServantX does not share your data with other organizations or use your claims data to train AI models.
                </p>
              </CardContent>
            </Card>
          </div>

          <Callout variant="warning">
            ServantX is a tool to support your billing team's compliance work. Your organization remains the HIPAA covered entity responsible for workforce training, Business Associate Agreements (BAAs), and overall compliance posture. Contact your compliance officer if you have specific questions about your obligations.
          </Callout>
        </section>

        <Separator />

        {/* ─── FAQ ─── */}
        <section>
          <SectionAnchor id="faq" />
          <SectionHeader
            icon={HelpCircle}
            title="FAQ & Troubleshooting"
            subtitle="Answers to the most common questions from billing teams."
          />

          <Accordion type="multiple" className="border rounded-lg divide-y overflow-hidden">
            <AccordionItem value="faq-duplicate" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">My upload said "duplicate file" — what does that mean?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  ServantX creates a unique fingerprint (SHA-256 hash) of every uploaded file. If you upload the same file twice, the second upload is automatically rejected to prevent duplicate audit records. This is expected behavior.
                </p>
                <p>
                  If you need to re-process the same file under a different pricing mode or after uploading a new contract, contact support — they can remove the fingerprint lock so you can re-upload.
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="faq-processing" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">My file uploaded but I don't see any documents. What's wrong?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>Processing takes time, especially for large files. Wait two to five minutes and refresh the Documents page. If after ten minutes you still see nothing:</p>
                <ul className="ml-4 list-disc space-y-1">
                  <li>Confirm the correct client workspace is active — documents only appear for the active client.</li>
                  <li>Check the Receipts page to confirm your upload shows a "Processed" or "Complete" status rather than "Failed."</li>
                  <li>If the receipt shows "Failed," the file may have a format issue. Verify the file is a valid .835 EDI file, not a PDF or Excel export of remittance data.</li>
                </ul>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="faq-no-flags" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">ServantX isn't flagging any underpayments for my commercial claims. Why?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>For commercial payers, ServantX uses your uploaded contract rules plus AI analysis. If no contract is uploaded for this payer, there is no benchmark to compare against — the system may default to Medicare rates, which can be lower than your negotiated contract rates.</p>
                <p>
                  <strong>Fix:</strong> Upload the payer contract in the Contracts section. Once extracted, re-upload or reprocess the affected 835 file to see contract-based findings. Also confirm your Pricing Mode is set to AUTO or CONTRACT in Settings.
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="faq-wrong-engine" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">The pricing engine used the wrong fee schedule for a claim. Can I fix it?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  In AUTO mode, ServantX reads the payer name from the 835 file to determine which engine to use. If a payer name is abbreviated or formatted differently than expected, the system may choose a suboptimal engine.
                </p>
                <p>
                  Options:
                </p>
                <ul className="ml-4 list-disc space-y-1">
                  <li>Switch to a specific Pricing Mode (MEDICARE or CONTRACT) in Settings and re-upload to force the correct engine.</li>
                  <li>In ALL mode, ServantX runs every engine and picks the highest variance result, which reduces the impact of misidentified payer types.</li>
                </ul>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="faq-appeal-letter" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">The generated appeal letter has the wrong amount or incorrect details. What should I do?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Appeal letters are AI-generated drafts and should always be reviewed before sending. If you find an error:
                </p>
                <ul className="ml-4 list-disc space-y-1">
                  <li>Download the letter and edit it in your word processor before submission.</li>
                  <li>Check the source claim detail page — if the underlying pricing data is incorrect, the issue is in the repricing engine, not the letter generator. Review the fee schedule comparison and AI reasoning to understand the discrepancy.</li>
                  <li>If you believe the system is systematically generating wrong amounts, contact support with a specific claim example.</li>
                </ul>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="faq-timely-filing" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Does ServantX track timely filing deadlines?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  ServantX does not currently track timely filing deadlines automatically. Filing deadlines vary by payer and contract and are your billing team's responsibility to monitor. When you generate an appeal letter, check your contract's appeal timely filing clause — this is something you can ask about using the Contract Chat feature.
                </p>
                <p>
                  As a general rule, most commercial payer contracts require appeals to be filed within 120–180 days of the initial remittance date. Medicare appeals have specific administrative law deadlines depending on claim type.
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="faq-csv" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">Can I share audit reports with my compliance officer or CFO?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Yes. Use the <strong>Export CSV</strong> button on the Documents page to download a spreadsheet of all audit findings. The ROI Dashboard can be reviewed directly in ServantX by anyone with an account on your organization's workspace.
                </p>
                <p>
                  If your CFO or compliance officer needs access, have them create their own account at www.servantx.ai — they can then be given access to the relevant client workspace.
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="faq-medicaid-state" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">I'm not in Texas — will Medicaid repricing work for my state?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Currently ServantX includes the Texas Medicaid Fee-for-Service schedule. Claims from other states that trigger the Medicaid engine fall back to CONTRACT + AI analysis. Additional state Medicaid fee schedules are on the product roadmap.
                </p>
                <p>
                  If you are outside Texas, set your Pricing Mode to AUTO or CONTRACT to get the best results with your uploaded payer contracts.
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="faq-data-loss" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">What happens if I accidentally delete a document or close the browser?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Closing your browser or navigating away does not delete anything. All data is saved server-side. Simply log back in and navigate to the Documents page — everything will be there.
                </p>
                <p>
                  If you intentionally delete a document and need it restored, contact ServantX support with the claim reference number. Deleted records are retained in backup storage for 30 days.
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="faq-contact" className="border-0 px-4">
              <AccordionTrigger className="font-semibold">How do I contact support?</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground space-y-2 pb-4">
                <p>
                  Email <strong>support@servantx.ai</strong> with a description of your issue, the client workspace name, and — if applicable — the claim reference number. Include a screenshot if helpful.
                </p>
                <p>
                  For urgent issues affecting active appeal deadlines, mark your email subject line <em>[URGENT]</em> and note the filing deadline in the body of your message.
                </p>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </section>

        {/* Footer */}
        <div className="pt-4 pb-8">
          <Separator className="mb-6" />
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              <span>Last updated: April 2026 · ServantX v2026</span>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              <span>HIPAA-compliant medical billing audit platform</span>
            </div>
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
}
