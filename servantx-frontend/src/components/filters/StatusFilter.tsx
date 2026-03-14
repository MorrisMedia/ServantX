import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { DocumentStatus } from "@/lib/types/document";
import { Filter } from "lucide-react";
import { useState } from "react";

interface StatusFilterProps {
  selectedStatuses: DocumentStatus[];
  onStatusChange: (statuses: DocumentStatus[]) => void;
}

const allStatuses: DocumentStatus[] = [
  DocumentStatus.NOT_SUBMITTED,
  DocumentStatus.IN_PROGRESS,
  DocumentStatus.SUCCEEDED,
  DocumentStatus.CANCELLED,
  DocumentStatus.DECLINED,
];

const statusLabels: Record<DocumentStatus, string> = {
  [DocumentStatus.NOT_SUBMITTED]: "Not Submitted",
  [DocumentStatus.IN_PROGRESS]: "In Progress",
  [DocumentStatus.SUCCEEDED]: "Succeeded",
  [DocumentStatus.CANCELLED]: "Cancelled",
  [DocumentStatus.DECLINED]: "Declined",
};

export function StatusFilter({ selectedStatuses, onStatusChange }: StatusFilterProps) {
  const [open, setOpen] = useState(false);
  const [tempStatuses, setTempStatuses] = useState<DocumentStatus[]>(selectedStatuses);

  const handleStatusToggle = (status: DocumentStatus) => {
    setTempStatuses((prev) =>
      prev.includes(status)
        ? prev.filter((s) => s !== status)
        : [...prev, status]
    );
  };

  const handleApply = () => {
    onStatusChange(tempStatuses);
    setOpen(false);
  };

  const handleClear = () => {
    setTempStatuses([]);
    onStatusChange([]);
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline">
          <Filter className="mr-2 h-4 w-4" />
          Status
          {selectedStatuses.length > 0 && (
            <span className="ml-2 rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
              {selectedStatuses.length}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56" align="start">
        <div className="space-y-4">
          <div className="space-y-2">
            {allStatuses.map((status) => (
              <div key={status} className="flex items-center space-x-2">
                <Checkbox
                  id={status}
                  checked={tempStatuses.includes(status)}
                  onCheckedChange={() => handleStatusToggle(status)}
                />
                <Label
                  htmlFor={status}
                  className="text-sm font-normal cursor-pointer"
                >
                  {statusLabels[status]}
                </Label>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <Button onClick={handleApply} className="flex-1" size="sm">Apply</Button>
            <Button onClick={handleClear} variant="outline" className="flex-1" size="sm">Clear</Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}



