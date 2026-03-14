import { format, formatDistanceToNow, isThisMonth, isThisYear, parseISO } from "date-fns";

export function formatDate(date: string | Date): string {
  const dateObj = typeof date === "string" ? parseISO(date) : date;
  return format(dateObj, "MMM d, yyyy");
}

export function formatDateTime(date: string | Date): string {
  const dateObj = typeof date === "string" ? parseISO(date) : date;
  return format(dateObj, "MMM d, yyyy 'at' h:mm a");
}

export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === "string" ? parseISO(date) : date;
  return formatDistanceToNow(dateObj, { addSuffix: true });
}

export function getThisMonthRange(): { from: Date; to: Date } {
  const now = new Date();
  const from = new Date(now.getFullYear(), now.getMonth(), 1);
  const to = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);
  return { from, to };
}

export function getThisYearRange(): { from: Date; to: Date } {
  const now = new Date();
  const from = new Date(now.getFullYear(), 0, 1);
  const to = new Date(now.getFullYear(), 11, 31, 23, 59, 59);
  return { from, to };
}

export function formatDateRange(from: Date, to: Date): string {
  return `${format(from, "MMM d")} - ${format(to, "MMM d, yyyy")}`;
}

export function isDateThisMonth(date: string | Date): boolean {
  const dateObj = typeof date === "string" ? parseISO(date) : date;
  return isThisMonth(dateObj);
}

export function isDateThisYear(date: string | Date): boolean {
  const dateObj = typeof date === "string" ? parseISO(date) : date;
  return isThisYear(dateObj);
}



