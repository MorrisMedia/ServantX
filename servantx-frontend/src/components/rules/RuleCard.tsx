import { Rule } from "@/lib/types/rule";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils/date";
import { Badge } from "@/components/ui/badge";
import { BookOpen, CheckCircle2, XCircle } from "lucide-react";

interface RuleCardProps {
  rule: Rule;
}

const typeLabels: Record<string, string> = {
  validation: "Validation",
  comparison: "Comparison",
  document: "Document",
  other: "Other",
};

export function RuleCard({ rule }: RuleCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-primary" />
              {rule.name}
            </CardTitle>
            <CardDescription className="mt-2">{rule.description}</CardDescription>
          </div>
          <div className="flex flex-col items-end gap-2">
            {rule.isActive ? (
              <Badge variant="default" className="flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Active
              </Badge>
            ) : (
              <Badge variant="outline" className="flex items-center gap-1">
                <XCircle className="h-3 w-3" />
                Inactive
              </Badge>
            )}
            <Badge variant="secondary">{typeLabels[rule.type] || rule.type}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          {rule.contractName && (
            <span>From: {rule.contractName}</span>
          )}
          <span>Created {formatDate(rule.createdAt)}</span>
        </div>
        {rule.conditions && Object.keys(rule.conditions).length > 0 && (
          <div className="mt-4 p-3 bg-muted rounded-lg">
            <p className="text-xs font-medium mb-2">Conditions:</p>
            <pre className="text-xs overflow-x-auto">
              {JSON.stringify(rule.conditions, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}



