// String formatting utilities

/**
 * Format a number as hex with optional padding
 * @param num The number to format
 * @param padLength Optional padding length (default: 2)
 * @returns Formatted hex string with 0x prefix
 */
export function toHex(num: number, padLength = 2): string {
  return `0x${num.toString(16).padStart(padLength, "0").toUpperCase()}`;
}

/**
 * Convert an array of numbers to a hex string
 * @param data Array of byte values
 * @returns Space-separated hex string
 */
export function bytesToHexString(data: number[]): string {
  return data
    .map((b) => b.toString(16).padStart(2, "0").toUpperCase())
    .join(" ");
}

/**
 * Format a file size in bytes to a human-readable string
 * @param bytes The size in bytes
 * @param decimals Number of decimal places (default: 1)
 * @returns Formatted size string (e.g., "1.5 MB")
 */
export function formatFileSize(bytes: number, decimals = 1): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${
    sizes[i]
  }`;
}

/**
 * Truncate a string to a maximum length with ellipsis
 * @param str The string to truncate
 * @param maxLength Maximum length (default: 50)
 * @returns Truncated string
 */
export function truncate(str: string, maxLength = 50): string {
  if (!str) return "";
  if (str.length <= maxLength) return str;
  return `${str.substring(0, maxLength - 3)}...`;
}
