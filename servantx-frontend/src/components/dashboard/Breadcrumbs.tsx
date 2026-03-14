import { useLocation } from "wouter";
import { ChevronRight, Home, HelpCircle } from "lucide-react";
import { Link } from "wouter";
import { cn } from "@/lib/utils";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
}

const routeLabels: Record<string, string> = {
  dashboard: "Dashboard",
  receipts: "Billing Records",
  "billing-records": "Billing Records",
  documents: "Documents",
  contracts: "Contracts",
  rules: "Rules",
  invoices: "Invoices",
  reports: "Reports",
  "audit-workflow": "Audit Workflow",
  settings: "Settings",
  upload: "Upload",
};

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  const [location] = useLocation();

  // Auto-generate breadcrumbs from route if not provided
  const breadcrumbItems: BreadcrumbItem[] = items || (() => {
    const parts = location.split("/").filter(Boolean);
    const result: BreadcrumbItem[] = [{ label: "Dashboard", href: "/dashboard" }];
    
    if (parts.length > 1 && parts[0] === "dashboard") {
      for (let i = 1; i < parts.length; i++) {
        const part = parts[i];
        const label = routeLabels[part] || part.charAt(0).toUpperCase() + part.slice(1);
        const href = i === parts.length - 1 ? undefined : `/${parts.slice(0, i + 1).join("/")}`;
        result.push({ label, href });
      }
    }
    
    return result;
  })();

  if (breadcrumbItems.length <= 1) {
    return null;
  }

  return (
    <nav className="flex items-center space-x-2 text-sm text-muted-foreground">
      <Link href="/dashboard" className="hover:text-foreground">
        <Home className="h-4 w-4" />
      </Link>
      {breadcrumbItems.map((item, index) => (
        <div key={index} className="flex items-center space-x-2">
          <ChevronRight className="h-4 w-4" />
          {item.href ? (
            <Link href={item.href} className="hover:text-foreground">
              {item.label}
            </Link>
          ) : (
            <span className={cn(index === breadcrumbItems.length - 1 && "text-foreground font-medium")}>
              {item.label}
            </span>
          )}
        </div>
      ))}
      <Link
        href="/dashboard/user-guide"
        className="ml-2 cursor-pointer hover:text-foreground transition-colors"
        aria-label="User Guide"
        title="User Guide"
      >
        <HelpCircle className="h-4 w-4" />
      </Link>
    </nav>
  );
}



