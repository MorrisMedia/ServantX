import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { X, Lightbulb } from "lucide-react";
import { useState } from "react";

interface OnboardingHintProps {
  title: string;
  description: string;
  onDismiss?: () => void;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function OnboardingHint({
  title,
  description,
  onDismiss,
  action,
}: OnboardingHintProps) {
  const [dismissed, setDismissed] = useState(false);

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss?.();
  };

  if (dismissed) return null;

  return (
    <Card className="border-primary/50 bg-primary/5">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">{title}</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDismiss}
            className="h-6 w-6"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      {action && (
        <CardContent>
          <Button onClick={action.onClick} size="sm">
            {action.label}
          </Button>
        </CardContent>
      )}
    </Card>
  );
}



