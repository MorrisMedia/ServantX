import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { CheckCircle2, Clock, FileX, XCircle } from "lucide-react";

interface StatusConfig {
  label: string;
  variant: "outline" | "secondary" | "default" | "destructive";
  icon: typeof FileX;
  description: string;
  color: string;
}

const defaultStatusConfig: StatusConfig = {
  label: "Not Submitted",
  variant: "outline",
  icon: FileX,
  description: "Document created but not yet sent for processing",
  color: "text-muted-foreground",
};

const statusConfig: Record<string, StatusConfig> = {
  not_submitted: defaultStatusConfig,
  in_progress: {
    label: "In Progress",
    variant: "secondary" as const,
    icon: Clock,
    description: "Document submitted and awaiting response",
    color: "text-yellow-600",
  },
  succeeded: {
    label: "Succeeded",
    variant: "default" as const,
    icon: CheckCircle2,
    description: "Payment received - amount has been paid",
    color: "text-green-600",
  },
  failed: {
    label: "Failed",
    variant: "destructive" as const,
    icon: XCircle,
    description: "Submission failed or was rejected",
    color: "text-red-600",
  },
};

interface StatusBadgeProps {
  status: string;
  showTooltip?: boolean;
}

export function StatusBadge({ status, showTooltip = true }: StatusBadgeProps) {
  const config = statusConfig[status] || defaultStatusConfig;
  const Icon = config.icon;

  const badge = (
    <Badge variant={config.variant} className="flex items-center gap-1.5">
      <Icon className={`h-3 w-3 ${config.color}`} />
      {config.label}
    </Badge>
  );

  if (!showTooltip) {
    return badge;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{badge}</TooltipTrigger>
        <TooltipContent>
          <p>{config.description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}



