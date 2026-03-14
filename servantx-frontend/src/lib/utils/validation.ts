export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function validateFileSize(file: File, maxSizeMB: number): boolean {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
}

export function validateFileType(file: File, allowedTypes: string[]): boolean {
  const normalizedType = (file.type || "").toLowerCase();
  const normalizedName = (file.name || "").toLowerCase();
  const extension = normalizedName.includes(".") ? `.${normalizedName.split(".").pop()}` : "";

  return allowedTypes.some((type) => {
    const normalizedAllowed = type.toLowerCase();
    if (normalizedAllowed.startsWith(".")) {
      return extension === normalizedAllowed;
    }
    return normalizedType === normalizedAllowed || normalizedType.includes(normalizedAllowed);
  });
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
}



