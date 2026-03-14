import { useQuery } from "@tanstack/react-query";
import { getRules } from "@/lib/api/rules";
import { RuleCard } from "./RuleCard";
import { RuleFilters } from "@/lib/types/rule";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { BookOpen } from "lucide-react";

interface RulesListProps {
  filters?: RuleFilters;
}

export function RulesList({ filters }: RulesListProps) {
  const { data: rules, isLoading, error } = useQuery({
    queryKey: ["/rules", filters],
    queryFn: () => getRules(filters),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-6 w-1/3 mb-2" />
              <Skeleton className="h-4 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-destructive">
            Failed to load rules. Please try again.
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!rules || rules.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No rules found</h3>
          <p className="text-sm text-muted-foreground">
            Rules will appear here after contracts are processed and rules are extracted.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {rules.map((rule) => (
        <RuleCard key={rule.id} rule={rule} />
      ))}
    </div>
  );
}



