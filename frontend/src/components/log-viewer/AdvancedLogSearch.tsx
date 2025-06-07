import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { Switch } from "@/components/ui/switch";
import { Search, Settings } from "lucide-react";
import { useState } from "react";
import { useLogViewer } from "./useLogViewer";

interface SearchOptions {
  caseSensitive: boolean;
  regex: boolean;
  searchInLogger: boolean;
  searchInTimestamp: boolean;
}

export function AdvancedLogSearch() {
  const { filters, updateFilters } = useLogViewer();
  const [searchOptions, setSearchOptions] = useState<SearchOptions>({
    caseSensitive: false,
    regex: false,
    searchInLogger: true,
    searchInTimestamp: false,
  });
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);

  const handleSearchChange = (value: string) => {
    // Store search options in the search string for processing
    // TODO: Enhance to pass full search data with options
    // const searchData = {
    //   query: value,
    //   options: searchOptions,
    // };

    // For now, just pass the query - could be enhanced to pass full search data
    updateFilters({ search: value });
  };

  const updateOption = (key: keyof SearchOptions, value: boolean) => {
    setSearchOptions(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="flex items-center gap-2">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search logs..."
          value={filters.search || ""}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="pl-10 pr-10"
          aria-label="Search logs"
        />
        <Popover open={isAdvancedOpen} onOpenChange={setIsAdvancedOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
              aria-label="Advanced search options"
            >
              <Settings className="h-3 w-3" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80" align="end">
            <div className="space-y-4">
              <h4 className="font-medium">Search Options</h4>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="case-sensitive" className="text-sm">
                    Case sensitive
                  </Label>
                  <Switch
                    id="case-sensitive"
                    checked={searchOptions.caseSensitive}
                    onCheckedChange={(checked) => updateOption('caseSensitive', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="regex" className="text-sm">
                    Regular expressions
                  </Label>
                  <Switch
                    id="regex"
                    checked={searchOptions.regex}
                    onCheckedChange={(checked) => updateOption('regex', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="search-logger" className="text-sm">
                    Search in logger names
                  </Label>
                  <Switch
                    id="search-logger"
                    checked={searchOptions.searchInLogger}
                    onCheckedChange={(checked) => updateOption('searchInLogger', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="search-timestamp" className="text-sm">
                    Search in timestamps
                  </Label>
                  <Switch
                    id="search-timestamp"
                    checked={searchOptions.searchInTimestamp}
                    onCheckedChange={(checked) => updateOption('searchInTimestamp', checked)}
                  />
                </div>
              </div>

              {searchOptions.regex && (
                <div className="p-2 bg-muted rounded text-xs text-muted-foreground">
                  <strong>Regex examples:</strong><br />
                  <code>error|warning</code> - Match "error" or "warning"<br />
                  <code>^\[.*\]</code> - Lines starting with brackets<br />
                  <code>\d{4}-\d{2}-\d{2}</code> - Date pattern
                </div>
              )}
            </div>
          </PopoverContent>
        </Popover>
      </div>
    </div>
  );
}
