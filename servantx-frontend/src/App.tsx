import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/dashboard/ProtectedRoute";
import { ContractRequiredRoute } from "./components/dashboard/ContractRequiredRoute";
import NotFound from "@/pages/not-found";
import Home from "@/pages/home";
import RequestPilot from "@/pages/request-pilot";
import Contact from "@/pages/contact";
import Privacy from "@/pages/privacy";
import Terms from "@/pages/terms";
import LoginPage from "@/pages/auth/login";
import RegisterPage from "@/pages/auth/register";
import ForgotPasswordPage from "@/pages/auth/forgot-password";
import DashboardPage from "@/pages/dashboard";
import BillingRecordsPage from "@/pages/dashboard/receipts";
import BillingRecordUploadPage from "@/pages/dashboard/receipts/upload";
import DocumentsPage from "@/pages/dashboard/documents";
import DocumentDetailPage from "@/pages/dashboard/documents/detail";
import ContractsPage from "@/pages/dashboard/contracts";
import RulesPage from "@/pages/dashboard/rules";
import InvoicesPage from "@/pages/dashboard/invoices";
import ReportsPage from "@/pages/dashboard/reports";
import SettingsPage from "@/pages/dashboard/settings";
import UserGuidePage from "@/pages/dashboard/user-guide";
import AuditWorkflowPage from "@/pages/dashboard/audit-workflow";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/request-pilot" component={RequestPilot} />
      <Route path="/contact" component={Contact} />
      <Route path="/privacy" component={Privacy} />
      <Route path="/terms" component={Terms} />
      <Route path="/auth/login" component={LoginPage} />
      <Route path="/login" component={LoginPage} />
      <Route path="/auth/register" component={RegisterPage} />
      <Route path="/register" component={RegisterPage} />
      <Route path="/auth/forgot-password" component={ForgotPasswordPage} />
      <Route path="/forgot-password" component={ForgotPasswordPage} />
      {/* Contracts page - accessible without contract (to allow upload) */}
      <Route path="/dashboard/contracts">
        <ProtectedRoute>
          <ContractRequiredRoute allowWithoutContractOn={["/dashboard/contracts"]}>
            <ContractsPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      
      {/* All other dashboard routes require contract */}
      <Route path="/dashboard/billing-records/upload">
        <ProtectedRoute>
          <ContractRequiredRoute allowWithoutContractOn={["/dashboard/receipts/upload", "/dashboard/billing-records/upload", "/dashboard/contracts", "/dashboard"]}>
            <BillingRecordUploadPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/documents/:id">
        <ProtectedRoute>
          <ContractRequiredRoute>
            <DocumentDetailPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/billing-records">
        <ProtectedRoute>
          <ContractRequiredRoute>
            <BillingRecordsPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      {/* Legacy aliases while route rename rolls out */}
      <Route path="/dashboard/receipts/upload">
        <ProtectedRoute>
          <ContractRequiredRoute allowWithoutContractOn={["/dashboard/receipts/upload", "/dashboard/billing-records/upload", "/dashboard/contracts", "/dashboard"]}>
            <BillingRecordUploadPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/receipts">
        <ProtectedRoute>
          <ContractRequiredRoute>
            <BillingRecordsPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/documents">
        <ProtectedRoute>
          <ContractRequiredRoute>
            <DocumentsPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/rules">
        <ProtectedRoute>
          <ContractRequiredRoute>
            <RulesPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/invoices">
        <ProtectedRoute>
          <ContractRequiredRoute>
            <InvoicesPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/reports">
        <ProtectedRoute>
          <ContractRequiredRoute>
            <ReportsPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/audit-workflow">
        <ProtectedRoute>
          <ContractRequiredRoute>
            <AuditWorkflowPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/user-guide">
        <ProtectedRoute>
          <UserGuidePage />
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/settings">
        <ProtectedRoute>
          <ContractRequiredRoute>
            <SettingsPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard">
        <ProtectedRoute>
          <ContractRequiredRoute allowWithoutContractOn={["/dashboard", "/dashboard/contracts", "/dashboard/receipts/upload", "/dashboard/billing-records/upload"]}>
            <DashboardPage />
          </ContractRequiredRoute>
        </ProtectedRoute>
      </Route>
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
