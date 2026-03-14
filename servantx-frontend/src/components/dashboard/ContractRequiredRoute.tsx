import { useEffect } from "react";
import { useLocation } from "wouter";
import { useContractCheck } from "@/lib/hooks/useContractCheck";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileCheck, AlertCircle } from "lucide-react";
import { Link } from "wouter";

interface ContractRequiredRouteProps {
  children: React.ReactNode;
  allowOnContractsPage?: boolean; // Allow access to contracts page even without contract
}

/**
 * Route guard that requires a contract to be uploaded before accessing protected routes.
 * Redirects to /dashboard/contracts if no contract exists.
 */
export function ContractRequiredRoute({ 
  children, 
  allowOnContractsPage = true 
}: ContractRequiredRouteProps) {
  const { hasContract, isLoading } = useContractCheck();
  const [location, setLocation] = useLocation();

  // Allow access to contracts page if allowOnContractsPage is true
  const isContractsPage = location === "/dashboard/contracts";
  const shouldAllowAccess = isContractsPage && allowOnContractsPage;

  useEffect(() => {
    // Don't redirect if we're already on contracts page or if still loading
    if (isLoading || shouldAllowAccess) {
      return;
    }

    // Redirect to contracts page if no contract exists
    if (!hasContract) {
      setLocation("/dashboard/contracts");
    }
  }, [hasContract, isLoading, setLocation, shouldAllowAccess]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Allow access to contracts page even without contract
  if (shouldAllowAccess) {
    return <>{children}</>;
  }

  // Block access if no contract exists
  if (!hasContract) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-yellow-100 dark:bg-yellow-900 p-2">
                <AlertCircle className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <CardTitle>Contract Required</CardTitle>
                <CardDescription>
                  You need to upload a contract before accessing this page
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              To use ServantX, you must first upload your contract. This allows us to extract rules and process your documents correctly.
            </p>
            <Button asChild className="w-full">
              <Link href="/dashboard/contracts">
                <FileCheck className="mr-2 h-4 w-4" />
                Upload Contract
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // User has contract, allow access
  return <>{children}</>;
}


