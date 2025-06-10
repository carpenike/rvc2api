import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Copy, Download, FileText, Share } from "lucide-react";
import { toast } from "sonner";
import type { LogEntry } from "./log-viewer-context";
import { useLogViewer } from "./useLogViewer";

export function LogExportActions() {
  const { logs, filters } = useLogViewer();

  const copyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success("Copied to clipboard");
    } catch (error) {
      toast.error("Failed to copy to clipboard");
      console.error("Copy failed:", error);
    }
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${filename}`);
  };

  const formatLogsAsText = () => {
    return logs
      .map((log: LogEntry) => `[${log.timestamp}] ${log.level.toUpperCase()} ${log.logger ? `(${log.logger})` : ""} ${log.message}`)
      .join("\n");
  };

  const formatLogsAsJSON = () => {
    return JSON.stringify(
      {
        exported_at: new Date().toISOString(),
        filters_applied: filters,
        total_logs: logs.length,
        logs: logs,
      },
      null,
      2
    );
  };

  const formatLogsAsCSV = () => {
    const headers = ["timestamp", "level", "logger", "message"];
    const csvRows = [
      headers.join(","),
      ...logs.map((log: LogEntry) => [
        `"${log.timestamp}"`,
        `"${log.level}"`,
        `"${log.logger || ""}"`,
        `"${log.message.replace(/"/g, '""')}"`,
      ].join(","))
    ];
    return csvRows.join("\n");
  };

  const generateFilename = (extension: string) => {
    const now = new Date();
    const timestamp = now.toISOString().split("T")[0];
    const filterSuffix = filters.level ? `_${filters.level}` : "";
    return `logs_${timestamp}${filterSuffix}.${extension}`;
  };

  const handleCopyAsText = () => {
    void copyToClipboard(formatLogsAsText());
  };

  const handleCopyAsJSON = () => {
    void copyToClipboard(formatLogsAsJSON());
  };

  const handleDownloadText = () => {
    downloadFile(formatLogsAsText(), generateFilename("txt"), "text/plain");
  };

  const handleDownloadJSON = () => {
    downloadFile(formatLogsAsJSON(), generateFilename("json"), "application/json");
  };

  const handleDownloadCSV = () => {
    downloadFile(formatLogsAsCSV(), generateFilename("csv"), "text/csv");
  };

  const handleShareLogs = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: "System Logs",
          text: `${logs.length} log entries`,
          files: [new File([formatLogsAsText()], generateFilename("txt"), { type: "text/plain" })],
        });
      } catch (error) {
        console.error("Share failed:", error);
        handleCopyAsText(); // Fallback to copy
      }
    } else {
      handleCopyAsText(); // Fallback for browsers without share API
    }
  };

  if (logs.length === 0) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Download className="h-4 w-4" />
          <span className="hidden sm:inline">Export</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuItem onClick={handleCopyAsText} className="gap-2">
          <Copy className="h-4 w-4" />
          Copy as Text
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleCopyAsJSON} className="gap-2">
          <Copy className="h-4 w-4" />
          Copy as JSON
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleDownloadText} className="gap-2">
          <FileText className="h-4 w-4" />
          Download as Text
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleDownloadJSON} className="gap-2">
          <FileText className="h-4 w-4" />
          Download as JSON
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleDownloadCSV} className="gap-2">
          <FileText className="h-4 w-4" />
          Download as CSV
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => void handleShareLogs()} className="gap-2">
          <Share className="h-4 w-4" />
          Share Logs
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
