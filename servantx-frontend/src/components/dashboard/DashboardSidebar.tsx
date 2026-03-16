import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { useContractCheck } from "@/lib/hooks/useContractCheck";
import { toast } from "sonner";
import {
  LayoutDashboard,
  FileText,
  FileCheck,
  Settings,
  Receipt,
  BarChart3,
  HelpCircle,
  Lock,
} from "lucide-react";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  requiresContract?: boolean;
}

const navItems: NavItem[] = [
  { title: "Overview", href: "/dashboard", icon: LayoutDashboard, requiresContract: true },
  { title: "Billing Records", href: "/dashboard/billing-records", icon: Receipt, requiresContract: true },
  { title: "Documents", href: "/dashboard/documents", icon: FileText, requiresContract: true },
  { title: "Contracts", href: "/dashboard/contracts", icon: FileCheck, requiresContract: false },
  { title: "Audit Workflow", href: "/dashboard/audit-workflow", icon: BarChart3, requiresContract: true },
  { title: "Reports", href: "/dashboard/reports", icon: BarChart3, requiresContract: true },
  { title: "Operations Guide", href: "/dashboard/user-guide", icon: HelpCircle, requiresContract: false },
  { title: "Settings", href: "/dashboard/settings", icon: Settings, requiresContract: false },
];

export function DashboardSidebar() {
  const [location] = useLocation();
  const { hasContract, isLoading } = useContractCheck();

  const handleDisabledClick = (e: React.MouseEvent, item: NavItem) => {
    if (item.requiresContract && !hasContract && !isLoading) {
      e.preventDefault();
      toast.error("Please upload a contract first", {
        description: "You need to upload at least one contract before accessing this section.",
      });
    }
  };

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card">
      <div className="flex h-16 items-center border-b px-6">
        <h2 className="text-lg font-semibold">ServantX</h2>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location === item.href || (item.href !== "/dashboard" && location.startsWith(item.href));
          const isDisabled = item.requiresContract && !hasContract && !isLoading;

          if (isDisabled) {
            return (
              <button
                key={item.href}
                onClick={(e) => handleDisabledClick(e, item)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  "text-muted-foreground/50 cursor-not-allowed"
                )}
              >
                <Icon className="h-5 w-5" />
                {item.title}
                <Lock className="h-3 w-3 ml-auto" />
              </button>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.title}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
