import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DocumentFilters } from "@/lib/types/document";
import { getThisMonthRange, getThisYearRange } from "@/lib/utils/date";
import { Search, X } from "lucide-react";
import { useEffect, useState } from "react";
import { DateRangeFilter } from "./DateRangeFilter";
import { StatusFilter } from "./StatusFilter";

interface FilterBarProps {
  filters: DocumentFilters;
  updateFilters: (newFilters: Partial<DocumentFilters>) => void;
  clearFilters: () => void;
  onFiltersChange?: () => void;
}

export function FilterBar({ filters, updateFilters, clearFilters, onFiltersChange }: FilterBarProps) {
  const [searchInput, setSearchInput] = useState(filters.search || "");

  useEffect(() => {
    setSearchInput(filters.search || "");
  }, [filters.search]);

  const hasActiveFilters =
    (filters.status && filters.status.length > 0) ||
    filters.dateFrom ||
    filters.dateTo ||
    filters.amountMin !== undefined ||
    filters.amountMax !== undefined ||
    filters.search ||
    filters.receiptId;

  const handleSearch = () => {
    updateFilters({ search: searchInput || undefined });
    onFiltersChange?.();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const handleClear = () => {
    setSearchInput("");
    clearFilters();
    onFiltersChange?.();
  };

  const setDateRange = (range: "thisMonth" | "thisYear") => {
    if (range === "thisMonth") {
      const { from, to } = getThisMonthRange();
      updateFilters({
        dateFrom: from.toISOString(),
        dateTo: to.toISOString(),
      });
    } else if (range === "thisYear") {
      const { from, to } = getThisYearRange();
      updateFilters({
        dateFrom: from.toISOString(),
        dateTo: to.toISOString(),
      });
    }
    onFiltersChange?.();
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search by name or billing record..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="pl-9"
            />
          </div>
          <Button onClick={handleSearch} variant="secondary">
            <Search className="h-4 w-4" />
          </Button>
        </div>

        <StatusFilter
          selectedStatuses={filters.status || []}
          onStatusChange={(statuses) => { updateFilters({ status: statuses }); onFiltersChange?.(); }}
        />

        <DateRangeFilter
          dateFrom={filters.dateFrom}
          dateTo={filters.dateTo}
          onDateChange={(from, to) => {
            updateFilters({
              dateFrom: from?.toISOString(),
              dateTo: to?.toISOString(),
            });
            onFiltersChange?.();
          }}
        />

        <Button
          variant="outline"
          size="sm"
          onClick={() => setDateRange("thisMonth")}
        >
          This Month
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setDateRange("thisYear")}
        >
          This Year
        </Button>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={handleClear}>
            <X className="mr-2 h-4 w-4" />
            Clear Filters
          </Button>
        )}
      </div>
    </div>
  );
}
