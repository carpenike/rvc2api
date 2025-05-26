/**
 * utils.js - Shared utility functions for rvc2api Web UI
 *
 * Author: Ryan Holt
 * Last updated: 2025-05-12
 */

/**
 * Shows a toast notification.
 * @param {string} message - The message to display.
 * @param {'info'|'success'|'warning'|'error'} [type='info'] - The type of toast.
 * @param {number} [duration=5000] - Duration in milliseconds to show the toast.
 */
export function showToast(message, type = "info", duration = 3000) {
  const toastContainer = document.getElementById("toast-container");
  if (!toastContainer) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.setAttribute("role", "alert");
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("show");
  }, 10);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, duration);
}

/**
 * Attempts to copy text to the clipboard using the Clipboard API if available,
 * otherwise falls back to a legacy execCommand method.
 * @param {string} text - The text to copy.
 * @returns {Promise<void>} Resolves if copy succeeded, rejects if failed.
 */
export async function copyToClipboard(text) {
  // Modern Clipboard API
  if (
    navigator.clipboard &&
    typeof navigator.clipboard.writeText === "function"
  ) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch (err) {
      // Fallback below
    }
  }
  // Legacy fallback: create a temporary textarea and execCommand
  return new Promise((resolve, reject) => {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    try {
      const successful = document.execCommand("copy");
      document.body.removeChild(textarea);
      if (successful) {
        resolve();
      } else {
        reject(new Error("execCommand('copy') failed"));
      }
    } catch (err) {
      document.body.removeChild(textarea);
      reject(err);
    }
  });
}
