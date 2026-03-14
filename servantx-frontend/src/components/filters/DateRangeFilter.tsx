import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { CalendarIcon, X } from "lucide-react";
import { format, parse, isValid } from "date-fns";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";

interface DateRangeFilterProps {
  dateFrom?: string;
  dateTo?: string;
  onDateChange: (from: Date | undefined, to: Date | undefined) => void;
}

export function DateRangeFilter({ dateFrom, dateTo, onDateChange }: DateRangeFilterProps) {
  const [fromDate, setFromDate] = useState<Date | undefined>(
    dateFrom ? new Date(dateFrom) : undefined
  );
  const [toDate, setToDate] = useState<Date | undefined>(
    dateTo ? new Date(dateTo) : undefined
  );
  const [fromDateInput, setFromDateInput] = useState<string>(
    dateFrom ? format(new Date(dateFrom), "yyyy-MM-dd") : ""
  );
  const [toDateInput, setToDateInput] = useState<string>(
    dateTo ? format(new Date(dateTo), "yyyy-MM-dd") : ""
  );
  const [open, setOpen] = useState(false);

  // Update input fields when dates change from calendar
  useEffect(() => {
    if (fromDate) {
      setFromDateInput(format(fromDate, "yyyy-MM-dd"));
    } else {
      setFromDateInput("");
    }
  }, [fromDate]);

  useEffect(() => {
    if (toDate) {
      setToDateInput(format(toDate, "yyyy-MM-dd"));
    } else {
      setToDateInput("");
    }
  }, [toDate]);

  // Update dates when input fields change
  const handleFromDateInputChange = (value: string) => {
    setFromDateInput(value);
    if (value) {
      const parsed = parse(value, "yyyy-MM-dd", new Date());
      if (isValid(parsed)) {
        setFromDate(parsed);
      }
    } else {
      setFromDate(undefined);
    }
  };

  const handleToDateInputChange = (value: string) => {
    setToDateInput(value);
    if (value) {
      const parsed = parse(value, "yyyy-MM-dd", new Date());
      if (isValid(parsed)) {
        setToDate(parsed);
      }
    } else {
      setToDate(undefined);
    }
  };

  const handleApply = () => {
    onDateChange(fromDate, toDate);
    setOpen(false);
  };

  const handleClear = () => {
    setFromDate(undefined);
    setToDate(undefined);
    setFromDateInput("");
    setToDateInput("");
    onDateChange(undefined, undefined);
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-[280px] justify-start text-left font-normal",
            !fromDate && !toDate && "text-muted-foreground"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {fromDate && toDate ? (
            <>
              {format(fromDate, "MMM d")} - {format(toDate, "MMM d, yyyy")}
            </>
          ) : fromDate ? (
            format(fromDate, "MMM d, yyyy")
          ) : (
            "Pick a date range"
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 max-w-[95vw] sm:max-w-none shadow-xl border-0" align="start" sideOffset={8}>
        <div className="p-5 sm:p-6 min-w-[320px] sm:min-w-[680px] bg-gradient-to-br from-background to-muted/20">
          {/* Header */}
          <div className="flex items-center justify-between mb-5 pb-3 border-b">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-md bg-primary/10">
                <CalendarIcon className="h-4 w-4 text-primary" />
              </div>
              <h3 className="font-semibold text-sm">Select Date Range</h3>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 hover:bg-muted"
              onClick={() => setOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Date Inputs Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-foreground uppercase tracking-wide">Start Date</label>
              <Input
                type="date"
                value={fromDateInput}
                onChange={(e) => handleFromDateInputChange(e.target.value)}
                className="w-full h-10 text-sm border-2 focus:border-primary transition-colors"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-foreground uppercase tracking-wide">End Date</label>
              <Input
                type="date"
                value={toDateInput}
                onChange={(e) => handleToDateInputChange(e.target.value)}
                className="w-full h-10 text-sm border-2 focus:border-primary transition-colors"
                min={fromDateInput || undefined}
              />
            </div>
          </div>

          {/* Calendars Side by Side */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-foreground uppercase tracking-wide">From</label>
              <div className="rounded-lg border-2 bg-card p-3 shadow-sm">
                <Calendar
                  mode="single"
                  selected={fromDate}
                  onSelect={(date) => {
                    setFromDate(date);
                    if (date) {
                      setFromDateInput(format(date, "yyyy-MM-dd"));
                    }
                  }}
                  className="rounded-md"
                classNames={{
                  months: "flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
                  month: "space-y-4 relative",
                  caption: "flex justify-center pt-1 relative items-center mb-3",
                  caption_label: "text-sm font-semibold",
                  nav: "absolute inset-x-0 bottom-0 flex w-full items-center justify-between gap-1 pt-2",
                  button_previous: "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100 hover:bg-accent rounded-md transition-all",
                  button_next: "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100 hover:bg-accent rounded-md transition-all",
                  table: "w-full border-collapse space-y-1",
                  head_row: "flex mb-2",
                  head_cell: "text-muted-foreground rounded-md w-9 font-medium text-[0.8rem]",
                  row: "flex w-full mt-1",
                  cell: "h-9 w-9 text-center text-sm p-0 relative [&:has([aria-selected].day-range-end)]:rounded-r-md [&:has([aria-selected].day-outside)]:bg-accent/50 [&:has([aria-selected])]:bg-accent first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md focus-within:relative focus-within:z-20",
                  day: "h-9 w-9 p-0 font-medium aria-selected:opacity-100 rounded-md transition-all hover:bg-accent",
                  day_selected: "bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground shadow-sm",
                  day_today: "bg-accent text-accent-foreground font-semibold",
                  day_outside: "day-outside text-muted-foreground opacity-50 aria-selected:bg-accent/50 aria-selected:text-muted-foreground aria-selected:opacity-30",
                  day_disabled: "text-muted-foreground opacity-50 cursor-not-allowed",
                  day_range_middle: "aria-selected:bg-accent aria-selected:text-accent-foreground",
                  day_hidden: "invisible",
                }}
              />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-foreground uppercase tracking-wide">To</label>
              <div className="rounded-lg border-2 bg-card p-3 shadow-sm">
                <Calendar
                  mode="single"
                  selected={toDate}
                  onSelect={(date) => {
                    setToDate(date);
                    if (date) {
                      setToDateInput(format(date, "yyyy-MM-dd"));
                    }
                  }}
                  disabled={(date) => fromDate ? date < fromDate : false}
                  className="rounded-md"
                classNames={{
                  months: "flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
                  month: "space-y-4 relative",
                  caption: "flex justify-center pt-1 relative items-center mb-3",
                  caption_label: "text-sm font-semibold",
                  nav: "absolute inset-x-0 bottom-0 flex w-full items-center justify-between gap-1 pt-2",
                  button_previous: "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100 hover:bg-accent rounded-md transition-all",
                  button_next: "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100 hover:bg-accent rounded-md transition-all",
                  table: "w-full border-collapse space-y-1",
                  head_row: "flex mb-2",
                  head_cell: "text-muted-foreground rounded-md w-9 font-medium text-[0.8rem]",
                  row: "flex w-full mt-1",
                  cell: "h-9 w-9 text-center text-sm p-0 relative [&:has([aria-selected].day-range-end)]:rounded-r-md [&:has([aria-selected].day-outside)]:bg-accent/50 [&:has([aria-selected])]:bg-accent first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md focus-within:relative focus-within:z-20",
                  day: "h-9 w-9 p-0 font-medium aria-selected:opacity-100 rounded-md transition-all hover:bg-accent",
                  day_selected: "bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground shadow-sm",
                  day_today: "bg-accent text-accent-foreground font-semibold",
                  day_outside: "day-outside text-muted-foreground opacity-50 aria-selected:bg-accent/50 aria-selected:text-muted-foreground aria-selected:opacity-30",
                  day_disabled: "text-muted-foreground opacity-50 cursor-not-allowed",
                  day_range_middle: "aria-selected:bg-accent aria-selected:text-accent-foreground",
                  day_hidden: "invisible",
                }}
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-5 border-t">
            <Button 
              onClick={handleClear} 
              variant="outline" 
              className="flex-1 h-10 font-medium hover:bg-muted transition-all"
            >
              Clear
            </Button>
            <Button 
              onClick={handleApply} 
              className="flex-1 h-10 font-medium shadow-sm hover:shadow-md transition-all"
            >
              Apply
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}



