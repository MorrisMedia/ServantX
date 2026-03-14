import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import { Skeleton } from "@/components/ui/skeleton";
import { deleteContract, getContracts, reprocessContract } from "@/lib/api/contracts";
import { formatDateTime } from "@/lib/utils/date";
import { formatFileSize } from "@/lib/utils/validation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Download, FileSearch, ShieldCheck, Trash2 } from "lucide-react";
import { toast } from "sonner";

interface EngineRunDetails {
  engineVersion: string | null;
  runAtIso: string | null;
  runRulesCount: number | null;
  warningLines: string[];
  rawNotes: string | null;
}

function parseEngineRunDetails(notes?: string | null): EngineRunDetails {
  const raw = (notes || "").trim();
  if (!raw) {
    return {
      engineVersion: null,
      runAtIso: null,
      runRulesCount: null,
      warningLines: [],
      rawNotes: null,
    };
  }

  const lines = raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  const engineLine = lines.find((line) => line.includes("Processed by"));
  const engineMatch = engineLine
    ? engineLine.match(/Processed by (.+?) at ([^\s]+) with (\d+) extracted rule\(s\)\.?/i)
    : null;

  const warningLines = lines.filter((line) => /(warning|warn|error|fail|exception)/i.test(line));

  return {
    engineVersion: engineMatch?.[1] || null,
    runAtIso: engineMatch?.[2] || null,
    runRulesCount: engineMatch?.[3] ? Number(engineMatch[3]) : null,
    warningLines,
    rawNotes: raw,
  };
}

export function ContractList() {
  const queryClient = useQueryClient();
  const { data: contracts, isLoading, error } = useQuery({
    queryKey: ["/contracts"],
    queryFn: getContracts,
    refetchInterval: (query) => {
      const data = query.state.data as Awaited<ReturnType<typeof getContracts>> | undefined;
      return data?.some((contract) => contract.status === "processing") ? 2000 : false;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteContract,
    onSuccess: () => {
      toast.success("Contract deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["/contracts"] });
      queryClient.invalidateQueries({ queryKey: ["/rules"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to delete contract");
    },
  });

  const reprocessMutation = useMutation({
    mutationFn: reprocessContract,
    onSuccess: (data) => {
      toast.success(data.message || "Contract reprocessing started");
      queryClient.invalidateQueries({ queryKey: ["/contracts"] });
      queryClient.invalidateQueries({ queryKey: ["/rules"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to reprocess contract");
    },
  });

  const handleDelete = (contractId: string) => {
    deleteMutation.mutate(contractId);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-6 w-1/3 mb-2" />
              <Skeleton className="h-4 w-1/2" />
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
            Failed to load contracts. Please try again.
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!contracts || contracts.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{contracts.length} contract(s) uploaded</p>
      </div>
      {contracts.map((contract) => (
        <Card key={contract.id} className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-lg">{contract.name}</CardTitle>
                <CardDescription className="mt-1">
                  {contract.fileName}
                  {contract.fileSize && ` • ${formatFileSize(contract.fileSize)}`}
                </CardDescription>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                  <span
                    className={`rounded-full px-2 py-0.5 ${
                      contract.status === "processed"
                        ? "bg-green-500/15 text-green-700"
                        : contract.status === "processing"
                        ? "bg-blue-500/15 text-blue-700"
                        : contract.status === "error"
                        ? "bg-destructive/15 text-destructive"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {contract.status === "processing" ? "Processing in engine..." : `Status: ${contract.status}`}
                  </span>
                  {typeof contract.rulesExtracted === "number" && (
                    <span className="rounded-full bg-muted px-2 py-0.5 text-muted-foreground">
                      Rules extracted: {contract.rulesExtracted}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Drawer>
                  <DrawerTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8" title="Engine run details">
                      <FileSearch className="h-4 w-4" />
                    </Button>
                  </DrawerTrigger>
                  <DrawerContent className="max-h-[90vh]">
                    {(() => {
                      const details = parseEngineRunDetails(contract.notes);
                      return (
                        <>
                          <DrawerHeader>
                            <DrawerTitle className="flex items-center gap-2">
                              <ShieldCheck className="h-4 w-4" />
                              Engine Run Details
                            </DrawerTitle>
                            <DrawerDescription>
                              Operational audit view for this contract's background extraction run.
                            </DrawerDescription>
                          </DrawerHeader>
                          <div className="px-4 pb-2 space-y-4 overflow-y-auto">
                            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                              <div className="rounded-md border p-3">
                                <p className="text-xs font-medium text-muted-foreground">Status</p>
                                <p className="text-sm mt-1">{contract.status}</p>
                              </div>
                              <div className="rounded-md border p-3">
                                <p className="text-xs font-medium text-muted-foreground">Rules Extracted</p>
                                <p className="text-sm mt-1">
                                  {typeof contract.rulesExtracted === "number" ? contract.rulesExtracted : "Pending"}
                                </p>
                              </div>
                              <div className="rounded-md border p-3">
                                <p className="text-xs font-medium text-muted-foreground">Run Reported Rule Count</p>
                                <p className="text-sm mt-1">
                                  {typeof details.runRulesCount === "number" ? details.runRulesCount : "Not recorded yet"}
                                </p>
                              </div>
                              <div className="rounded-md border p-3">
                                <p className="text-xs font-medium text-muted-foreground">Engine Version</p>
                                <p className="text-sm mt-1">{details.engineVersion || "Not recorded yet"}</p>
                              </div>
                              <div className="rounded-md border p-3">
                                <p className="text-xs font-medium text-muted-foreground">Last Engine Run</p>
                                <p className="text-sm mt-1">
                                  {details.runAtIso ? formatDateTime(details.runAtIso) : "Not recorded yet"}
                                </p>
                              </div>
                            </div>

                            {details.warningLines.length > 0 ? (
                              <div className="rounded-md border border-yellow-500/30 bg-yellow-500/10 p-3">
                                <p className="text-xs font-semibold text-yellow-800 flex items-center gap-1">
                                  <AlertTriangle className="h-3.5 w-3.5" />
                                  Extraction Warnings
                                </p>
                                <ul className="mt-2 space-y-1 text-xs text-yellow-900">
                                  {details.warningLines.map((line, idx) => (
                                    <li key={`${contract.id}-warn-${idx}`}>- {line}</li>
                                  ))}
                                </ul>
                              </div>
                            ) : (
                              <div className="rounded-md border border-green-500/30 bg-green-500/10 p-3 text-xs text-green-800">
                                No extraction warnings were detected in this run.
                              </div>
                            )}

                            <div className="rounded-md border p-3">
                              <p className="text-xs font-medium text-muted-foreground mb-2">Raw Engine Notes</p>
                              <pre className="text-xs whitespace-pre-wrap break-words">
                                {details.rawNotes || "No notes recorded yet."}
                              </pre>
                            </div>
                          </div>
                          <DrawerFooter>
                            <Button
                              onClick={() => reprocessMutation.mutate(contract.id)}
                              disabled={reprocessMutation.isPending || contract.status === "processing"}
                            >
                              {reprocessMutation.isPending ? "Reprocessing..." : "Re-run Engine"}
                            </Button>
                            <p className="text-xs text-muted-foreground">
                              Processing runs in the backend and continues even if you leave this page after upload completes.
                            </p>
                            <DrawerClose asChild>
                              <Button variant="outline">Close</Button>
                            </DrawerClose>
                          </DrawerFooter>
                        </>
                      );
                    })()}
                  </DrawerContent>
                </Drawer>
                {contract.fileUrl && (
                  <Button
                    variant="ghost"
                    size="icon"
                    asChild
                    className="h-8 w-8"
                  >
                    <a href={contract.fileUrl} target="_blank" rel="noopener noreferrer" title="Download">
                      <Download className="h-4 w-4" />
                    </a>
                  </Button>
                )}
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Delete Contract</AlertDialogTitle>
                      <AlertDialogDescription>
                        Are you sure you want to delete "{contract.name}"? This action cannot be undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={() => handleDelete(contract.id)}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      >
                        Delete
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Uploaded on {formatDateTime(contract.uploadedAt)}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}



