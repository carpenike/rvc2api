import { AppLayout } from "@/components/app-layout";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BookOpen, ExternalLink, FileText, Search, Server } from "lucide-react";
import { useState, useEffect } from "react";

interface SearchResult {
  title: string;
  content: string;
  score: number;
  page?: string;
  section?: string;
}

interface DocumentationStatus {
  search_enabled: boolean;
  vector_store_status: string;
  total_documents: number;
  last_updated?: string;
}

export default function Documentation() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [docStatus, setDocStatus] = useState<DocumentationStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);

  // Simulate search functionality (would connect to /api/docs/search)
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setSearchError(null);

    try {
      const response = await fetch(
        `/api/docs/search?query=${encodeURIComponent(searchQuery)}&k=5`
      );

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const results: SearchResult[] = await response.json();
      setSearchResults(results);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "Search failed");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Load documentation service status
  const loadDocStatus = async () => {
    setStatusLoading(true);
    try {
      const response = await fetch("/api/docs/status");
      if (response.ok) {
        const status: DocumentationStatus = await response.json();
        setDocStatus(status);
      }
    } catch (error) {
      console.error("Failed to load documentation status:", error);
    } finally {
      setStatusLoading(false);
    }
  };

  // Load status on component mount
  useEffect(() => {
    void loadDocStatus();
  }, []);

  return (
    <AppLayout>
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Documentation</h1>
          <p className="text-muted-foreground">
            Browse and search the comprehensive RV-C documentation and API reference
          </p>
        </div>

        <Tabs defaultValue="search" className="space-y-6">
          <TabsList>
            <TabsTrigger value="search">
              <Search className="mr-2 h-4 w-4" />
              Search
            </TabsTrigger>
            <TabsTrigger value="api">
              <Server className="mr-2 h-4 w-4" />
              API Reference
            </TabsTrigger>
            <TabsTrigger value="guides">
              <BookOpen className="mr-2 h-4 w-4" />
              Guides
            </TabsTrigger>
          </TabsList>

          {/* Search Tab */}
          <TabsContent value="search" className="space-y-6">
            {/* Search Interface */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5" />
                  Documentation Search
                </CardTitle>
                <CardDescription>
                  Search through RV-C specifications, API documentation, and guides using
                  vector-based semantic search
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Search documentation... (e.g., 'lighting control', 'CAN bus setup')"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && void handleSearch()}
                    className="flex-1"
                  />
                  <Button onClick={() => void handleSearch()} disabled={isSearching || !searchQuery.trim()}>
                    {isSearching ? "Searching..." : "Search"}
                  </Button>
                </div>

                {/* Search Status */}
                {statusLoading ? (
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-4 w-4 rounded-full" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                ) : docStatus ? (
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <Badge variant={docStatus.search_enabled ? "default" : "secondary"}>
                      {docStatus.search_enabled ? "Search Enabled" : "Search Disabled"}
                    </Badge>
                    <span>
                      Vector Store: {docStatus.vector_store_status}
                    </span>
                    <span>
                      Documents: {docStatus.total_documents.toLocaleString()}
                    </span>
                    {docStatus.last_updated && (
                      <span>
                        Updated: {new Date(docStatus.last_updated).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                ) : null}
              </CardContent>
            </Card>

            {/* Search Results */}
            {searchError && (
              <Alert variant="destructive">
                <AlertDescription>{searchError}</AlertDescription>
              </Alert>
            )}

            {searchResults.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">
                  Search Results ({searchResults.length})
                </h3>
                {searchResults.map((result, index) => (
                  <Card key={index}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-4">
                        <div className="space-y-1 flex-1">
                          <CardTitle className="text-base">
                            {result.title || "Untitled"}
                          </CardTitle>
                          {result.page && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <FileText className="h-3 w-3" />
                              <span>{result.page}</span>
                              {result.section && (
                                <>
                                  <span>•</span>
                                  <span>{result.section}</span>
                                </>
                              )}
                            </div>
                          )}
                        </div>
                        <Badge variant="outline">
                          {Math.round(result.score * 100)}% match
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground line-clamp-3">
                        {result.content}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {searchQuery && !isSearching && searchResults.length === 0 && !searchError && (
              <Card>
                <CardContent className="text-center py-8">
                  <p className="text-muted-foreground">
                    No results found for "{searchQuery}"
                  </p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Try different keywords or check the guides section for common topics
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* API Reference Tab */}
          <TabsContent value="api" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              {/* Interactive API Docs */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Server className="h-5 w-5" />
                    Interactive API Documentation
                  </CardTitle>
                  <CardDescription>
                    Explore and test API endpoints directly in your browser
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Button
                      className="w-full justify-start"
                      variant="outline"
                      onClick={() => window.open("/docs", "_blank")}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Swagger UI Documentation
                    </Button>
                    <Button
                      className="w-full justify-start"
                      variant="outline"
                      onClick={() => window.open("/redoc", "_blank")}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      ReDoc Documentation
                    </Button>
                  </div>
                  <Separator />
                  <div className="text-sm text-muted-foreground">
                    <p>Access comprehensive API documentation with:</p>
                    <ul className="mt-2 space-y-1 ml-4">
                      <li>• Interactive endpoint testing</li>
                      <li>• Request/response examples</li>
                      <li>• Schema validation</li>
                      <li>• Authentication details</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* OpenAPI Schema */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    OpenAPI Schema
                  </CardTitle>
                  <CardDescription>
                    Download the machine-readable API specification
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Button
                      className="w-full justify-start"
                      variant="outline"
                      onClick={() => window.open("/openapi.json", "_blank")}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      OpenAPI JSON Schema
                    </Button>
                    <Button
                      className="w-full justify-start"
                      variant="outline"
                      onClick={() => window.open("/api/docs/openapi", "_blank")}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      API Schema Endpoint
                    </Button>
                  </div>
                  <Separator />
                  <div className="text-sm text-muted-foreground">
                    <p>Use the OpenAPI schema to:</p>
                    <ul className="mt-2 space-y-1 ml-4">
                      <li>• Generate API clients</li>
                      <li>• Import into Postman/Insomnia</li>
                      <li>• Validate requests</li>
                      <li>• Generate mock data</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* API Categories */}
            <Card>
              <CardHeader>
                <CardTitle>API Categories</CardTitle>
                <CardDescription>
                  Overview of available API endpoint groups
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  <div className="space-y-2">
                    <h4 className="font-medium">Entities</h4>
                    <p className="text-sm text-muted-foreground">
                      Manage and control RV-C devices like lights, tanks, and sensors
                    </p>
                    <Badge variant="secondary">/api/entities</Badge>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">CAN Bus</h4>
                    <p className="text-sm text-muted-foreground">
                      Direct CAN bus interface, message sending, and statistics
                    </p>
                    <Badge variant="secondary">/api/can</Badge>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">Configuration</h4>
                    <p className="text-sm text-muted-foreground">
                      System configuration, status, and health monitoring
                    </p>
                    <Badge variant="secondary">/api/config</Badge>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">WebSocket</h4>
                    <p className="text-sm text-muted-foreground">
                      Real-time updates and bidirectional communication
                    </p>
                    <Badge variant="secondary">/ws</Badge>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">Documentation</h4>
                    <p className="text-sm text-muted-foreground">
                      Search and access RV-C specification documentation
                    </p>
                    <Badge variant="secondary">/api/docs</Badge>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">Diagnostics</h4>
                    <p className="text-sm text-muted-foreground">
                      Unknown PGNs, unmapped entries, and system diagnostics
                    </p>
                    <Badge variant="secondary">/api/entities/unknown-pgns</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Guides Tab */}
          <TabsContent value="guides" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              {/* Quick Start */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Start Guide</CardTitle>
                  <CardDescription>
                    Get up and running with CoachIQ
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium mt-0.5">
                        1
                      </div>
                      <div>
                        <p className="font-medium">Setup Environment</p>
                        <p className="text-muted-foreground">
                          Install dependencies with Poetry and configure CAN interfaces
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium mt-0.5">
                        2
                      </div>
                      <div>
                        <p className="font-medium">Connect Devices</p>
                        <p className="text-muted-foreground">
                          Configure RV-C device mappings and areas
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium mt-0.5">
                        3
                      </div>
                      <div>
                        <p className="font-medium">Control & Monitor</p>
                        <p className="text-muted-foreground">
                          Use the web interface or API to control and monitor devices
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Common Topics */}
              <Card>
                <CardHeader>
                  <CardTitle>Common Topics</CardTitle>
                  <CardDescription>
                    Frequently accessed documentation sections
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {[
                      "CAN bus configuration",
                      "Device entity mapping",
                      "Light control commands",
                      "WebSocket integration",
                      "API authentication",
                      "Troubleshooting connectivity",
                    ].map((topic, index) => (
                      <Button
                        key={index}
                        variant="ghost"
                        className="w-full justify-start h-auto p-2"
                        onClick={() => {
                          setSearchQuery(topic);
                          void handleSearch();
                        }}
                      >
                        <Search className="mr-2 h-3 w-3" />
                        <span className="text-sm">{topic}</span>
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Development Resources */}
              <Card>
                <CardHeader>
                  <CardTitle>Development Resources</CardTitle>
                  <CardDescription>
                    Tools and resources for developers
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => window.open("https://github.com/carpenike/coachiq", "_blank")}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      GitHub Repository
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => window.open("/api/config/spec", "_blank")}
                    >
                      <FileText className="mr-2 h-4 w-4" />
                      RV-C Specification
                    </Button>
                  </div>
                  <Separator />
                  <div className="text-sm text-muted-foreground">
                    <p>Additional resources:</p>
                    <ul className="mt-2 space-y-1 ml-4">
                      <li>• Example API requests</li>
                      <li>• WebSocket client examples</li>
                      <li>• Device integration guides</li>
                      <li>• Troubleshooting checklist</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* Support */}
              <Card>
                <CardHeader>
                  <CardTitle>Support & Community</CardTitle>
                  <CardDescription>
                    Get help and connect with the community
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Alert>
                    <BookOpen className="h-4 w-4" />
                    <AlertDescription>
                      For technical support, check the search results above or browse the
                      interactive API documentation for detailed endpoint information.
                    </AlertDescription>
                  </Alert>
                  <div className="text-sm text-muted-foreground">
                    <p>Community resources:</p>
                    <ul className="mt-2 space-y-1 ml-4">
                      <li>• GitHub Issues for bug reports</li>
                      <li>• GitHub Discussions for questions</li>
                      <li>• Pull requests for contributions</li>
                      <li>• Documentation improvements</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
