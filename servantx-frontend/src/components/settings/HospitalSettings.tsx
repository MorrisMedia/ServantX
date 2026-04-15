import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Settings2 } from "lucide-react";
import { getHospitalPricingConfig, updateHospitalPricingConfig } from "@/lib/api/hospitals";
import type { PricingMode } from "@/lib/types/hospital";

const PRICING_MODE_LABELS: Record<PricingMode, string> = {
  AUTO: "Auto",
  MEDICARE: "Medicare",
  MEDICAID: "Medicaid",
  CONTRACT: "Contract",
  ALL: "All Engines",
};

const PRICING_MODE_DESCRIPTIONS: Record<PricingMode, string> = {
  AUTO: "Detect from billing record payer (recommended)",
  MEDICARE: "Always use Medicare fee schedules (MPFS/IPPS/OPPS)",
  MEDICAID: "Always use state Medicaid fee schedule",
  CONTRACT: "Use uploaded contract rules + AI analysis",
  ALL: "Run all engines, surface highest underpayment",
};

export function HospitalPricingSettings() {
  const queryClient = useQueryClient();
  const [pricingMode, setPricingMode] = useState<PricingMode | "">("");
  const [state, setState] = useState("");
  const [initialized, setInitialized] = useState(false);

  const { data: config, isLoading } = useQuery({
    queryKey: ["/auth/hospital/config"],
    queryFn: getHospitalPricingConfig,
    onSuccess: (data) => {
      if (!initialized) {
        setPricingMode(data.pricing_mode);
        setState(data.state || "");
        setInitialized(true);
      }
    },
  } as any);

  // Initialize form from fetched data if not yet done
  if (config && !initialized) {
    setPricingMode(config.pricing_mode);
    setState(config.state || "");
    setInitialized(true);
  }

  const saveMutation = useMutation({
    mutationFn: () =>
      updateHospitalPricingConfig({
        pricing_mode: pricingMode as PricingMode,
        state: state.toUpperCase().slice(0, 2),
      }),
    onSuccess: () => {
      toast.success("Pricing configuration saved");
      queryClient.invalidateQueries({ queryKey: ["/auth/hospital/config"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to save pricing configuration");
    },
  });

  const handleSave = () => {
    if (!pricingMode) {
      toast.error("Please select a pricing mode");
      return;
    }
    saveMutation.mutate();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="h-5 w-5" />
          Pricing Engine Configuration
        </CardTitle>
        <CardDescription>
          Control which repricing engine ServantX uses when analyzing billing records
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading configuration...
          </div>
        ) : (
          <>
            <div className="space-y-2">
              <Label htmlFor="pricing-mode">Pricing Mode</Label>
              <Select
                value={pricingMode}
                onValueChange={(val) => setPricingMode(val as PricingMode)}
              >
                <SelectTrigger id="pricing-mode">
                  <SelectValue placeholder="Select a pricing mode" />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(PRICING_MODE_LABELS) as PricingMode[]).map((mode) => (
                    <SelectItem key={mode} value={mode}>
                      <div className="flex flex-col">
                        <span className="font-medium">{PRICING_MODE_LABELS[mode]}</span>
                        <span className="text-xs text-muted-foreground">
                          {PRICING_MODE_DESCRIPTIONS[mode]}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {pricingMode && (
                <p className="text-sm text-muted-foreground">
                  {PRICING_MODE_DESCRIPTIONS[pricingMode as PricingMode]}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="state">State</Label>
              <Input
                id="state"
                value={state}
                onChange={(e) => setState(e.target.value.toUpperCase().slice(0, 2))}
                placeholder="TX"
                maxLength={2}
                className="w-24 uppercase"
              />
              <p className="text-xs text-muted-foreground">
                2-letter state code used for Medicaid fee schedules
              </p>
            </div>

            <Button
              onClick={handleSave}
              disabled={saveMutation.isPending || !pricingMode}
            >
              {saveMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Configuration"
              )}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
