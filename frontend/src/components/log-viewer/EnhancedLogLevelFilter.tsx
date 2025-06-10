import { Button } from "@/components/ui/button";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";
import type { LogFilters } from "./log-viewer-context";
import { useLogViewer } from "./useLogViewer";

const LEVELS = [
  { value: "", label: "All Levels", description: "Show all log levels" },
  { value: "0", label: "Emergency", description: "System is unusable" },
  { value: "1", label: "Alert", description: "Action must be taken immediately" },
  { value: "2", label: "Critical", description: "Critical conditions" },
  { value: "3", label: "Error", description: "Error conditions" },
  { value: "4", label: "Warning", description: "Warning conditions" },
  { value: "5", label: "Notice", description: "Normal but significant condition" },
  { value: "6", label: "Info", description: "Informational messages" },
  { value: "7", label: "Debug", description: "Debug-level messages" },
];

export function EnhancedLogLevelFilter() {
  const { filters, updateFilters } = useLogViewer();
  const [open, setOpen] = useState(false);

  const currentLevel = LEVELS.find(level => level.value === (filters.level || ""));

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[200px] justify-between"
        >
          {currentLevel?.label || "All Levels"}
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[250px] p-0">
        <Command>
          <CommandInput placeholder="Search log levels..." />
          <CommandList>
            <CommandEmpty>No log level found.</CommandEmpty>
            <CommandGroup>
              <ScrollArea className="h-[200px]">
                {LEVELS.map((level) => (
                  <CommandItem
                    key={level.value}
                    value={level.value}
                    onSelect={() => {
                      const filters: Partial<LogFilters> = {};
                      if (level.value) {
                        filters.level = level.value;
                      }
                      updateFilters(filters);
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={`mr-2 h-4 w-4 ${
                        currentLevel?.value === level.value ? "opacity-100" : "opacity-0"
                      }`}
                    />
                    <div className="flex flex-col">
                      <span className="font-medium">{level.label}</span>
                      <span className="text-xs text-muted-foreground">
                        {level.description}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </ScrollArea>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
