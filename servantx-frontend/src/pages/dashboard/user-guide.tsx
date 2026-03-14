import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, Loader2 } from "lucide-react";
import { useState } from "react";

export default function UserGuidePage() {
  const [isLoading, setIsLoading] = useState(true);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">User Guide</h1>
          <p className="text-muted-foreground">
            Learn how to use ServantX with our interactive guide.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Interactive Guide
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="w-full flex justify-center">
              <div className="w-full max-w-4xl relative" style={{ aspectRatio: '4/3' }}>
                {isLoading && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-muted/50 rounded-lg z-10">
                    <div className="flex flex-col items-center gap-4 p-8">
                      <div className="relative">
                        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                          <BookOpen className="h-8 w-8 text-primary animate-pulse" />
                        </div>
                        <Loader2 className="h-6 w-6 text-primary animate-spin absolute -bottom-1 -right-1" />
                      </div>
                      <div className="text-center">
                        <p className="font-medium text-foreground">Loading Guide</p>
                        <p className="text-sm text-muted-foreground">Please wait while we prepare the interactive guide...</p>
                      </div>
                    </div>
                  </div>
                )}
                <iframe
                  src="https://www.usebreadcrumb.com/embed/paBLZ67yeE8"
                  className="w-full h-full rounded-lg border"
                  frameBorder="0"
                  allowFullScreen
                  onLoad={() => setIsLoading(false)}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
