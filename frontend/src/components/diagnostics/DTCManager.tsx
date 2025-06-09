/**
 * DTC Manager Component
 *
 * Advanced diagnostic trouble code management interface with filtering,
 * sorting, resolution capabilities, and real-time updates following
 * modern CAN bus diagnostic UI patterns.
 */

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
    AlertCircle,
    CheckCircle,
    Eye,
    RefreshCw,
    Search,
    Shield,
    SortAsc,
    SortDesc
} from 'lucide-react';
import React, { useMemo, useState } from 'react';
import { toast } from 'sonner';

import { fetchActiveDTCs, resolveDTC } from '@/api/endpoints';
import type { DTCFilters, DiagnosticTroubleCode } from '@/api/types';

interface DTCManagerProps {
  showFilters?: boolean;
  showActions?: boolean;
  maxHeight?: string;
  compact?: boolean;
  autoRefresh?: boolean;
  onDTCSelect?: (dtc: DiagnosticTroubleCode) => void;
}

// Utility functions
const getSeverityVariant = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'critical': return 'destructive';
    case 'high': return 'destructive';
    case 'medium': return 'secondary';
    case 'low': return 'outline';
    default: return 'outline';
  }
};


const getProtocolColor = (protocol: string) => {
  switch (protocol.toLowerCase()) {
    case 'rvc': return 'bg-blue-100 text-blue-800';
    case 'j1939': return 'bg-green-100 text-green-800';
    case 'firefly': return 'bg-purple-100 text-purple-800';
    case 'spartan_k2': return 'bg-orange-100 text-orange-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

// DTC Detail Dialog Component
const DTCDetailDialog: React.FC<{
  dtc: DiagnosticTroubleCode | null;
  isOpen: boolean;
  onClose: () => void;
  onResolve?: (dtc: DiagnosticTroubleCode) => void;
}> = ({ dtc, isOpen, onClose, onResolve }) => {
  if (!dtc) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            DTC Details: {dtc.code}
          </DialogTitle>
          <DialogDescription>
            Diagnostic trouble code information and resolution options
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Header Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge className={getProtocolColor(dtc.protocol)}>
                  {dtc.protocol.toUpperCase()}
                </Badge>
                <Badge variant={getSeverityVariant(dtc.severity)}>
                  {dtc.severity}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                System: {dtc.system_type.replace(/_/g, ' ')}
              </p>
            </div>
            <div className="text-right space-y-1">
              <div className="text-sm text-muted-foreground">Source Address</div>
              <div className="font-mono font-medium">0x{dtc.source_address.toString(16).toUpperCase()}</div>
              {dtc.pgn && (
                <>
                  <div className="text-sm text-muted-foreground">PGN</div>
                  <div className="font-mono font-medium">0x{dtc.pgn.toString(16).toUpperCase()}</div>
                </>
              )}
            </div>
          </div>

          <Separator />

          {/* Description */}
          <div>
            <h4 className="font-medium mb-2">Description</h4>
            <p className="text-sm text-muted-foreground bg-gray-50 p-3 rounded">
              {dtc.description || 'No description available'}
            </p>
          </div>

          {/* Occurrence Information */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 rounded border">
              <div className="text-2xl font-bold">{dtc.count}</div>
              <div className="text-xs text-muted-foreground">Occurrences</div>
            </div>
            <div className="text-center p-3 rounded border">
              <div className="text-sm font-medium">
                {new Date(dtc.first_seen).toLocaleDateString()}
              </div>
              <div className="text-xs text-muted-foreground">First Seen</div>
            </div>
            <div className="text-center p-3 rounded border">
              <div className="text-sm font-medium">
                {new Date(dtc.last_seen).toLocaleDateString()}
              </div>
              <div className="text-xs text-muted-foreground">Last Seen</div>
            </div>
          </div>

          {/* Metadata */}
          {Object.keys(dtc.metadata).length > 0 && (
            <>
              <Separator />
              <div>
                <h4 className="font-medium mb-2">Additional Information</h4>
                <div className="space-y-1 text-sm">
                  {Object.entries(dtc.metadata).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-muted-foreground capitalize">
                        {key.replace(/_/g, ' ')}:
                      </span>
                      <span className="font-mono">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          {!dtc.resolved && onResolve && (
            <Button onClick={() => onResolve(dtc)}>
              Mark as Resolved
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Main DTC Manager Component
export const DTCManager: React.FC<DTCManagerProps> = ({
  showFilters = true,
  showActions = true,
  maxHeight = "600px",
  compact = false,
  autoRefresh = true,
  onDTCSelect
}) => {
  const [filters, setFilters] = useState<DTCFilters>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof DiagnosticTroubleCode>('last_seen');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [selectedDTC, setSelectedDTC] = useState<DiagnosticTroubleCode | null>(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);


  // Fetch DTCs with filters
  const { data: dtcData, isLoading, error, refetch } = useQuery({
    queryKey: ['diagnostics', 'active-dtcs', filters],
    queryFn: () => fetchActiveDTCs(filters),
    refetchInterval: autoRefresh ? 15000 : false,
  });

  // Resolve DTC mutation
  const resolveMutation = useMutation({
    mutationFn: (dtc: DiagnosticTroubleCode) =>
      resolveDTC(dtc.protocol, parseInt(dtc.code), dtc.source_address),
    onSuccess: () => {
      toast.success('DTC resolved successfully');
      refetch();
      setShowDetailDialog(false);
    },
    onError: (error) => {
      toast.error('Failed to resolve DTC: ' + (error as Error).message);
    },
  });

  // Filter and sort DTCs
  const filteredAndSortedDTCs = useMemo(() => {
    if (!dtcData?.dtcs) return [];

    const filtered = dtcData.dtcs.filter(dtc => {
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return (
          dtc.code.toLowerCase().includes(searchLower) ||
          dtc.description.toLowerCase().includes(searchLower) ||
          dtc.system_type.toLowerCase().includes(searchLower) ||
          dtc.protocol.toLowerCase().includes(searchLower)
        );
      }
      return true;
    });

    // Sort the filtered results
    filtered.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue);
        return sortDirection === 'asc' ? comparison : -comparison;
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        const comparison = aValue - bValue;
        return sortDirection === 'asc' ? comparison : -comparison;
      }

      return 0;
    });

    return filtered;
  }, [dtcData?.dtcs, searchTerm, sortField, sortDirection]);

  const handleSort = (field: keyof DiagnosticTroubleCode) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const handleDTCSelect = (dtc: DiagnosticTroubleCode) => {
    setSelectedDTC(dtc);
    if (onDTCSelect) {
      onDTCSelect(dtc);
    } else {
      setShowDetailDialog(true);
    }
  };

  const handleResolveDTC = (dtc: DiagnosticTroubleCode) => {
    resolveMutation.mutate(dtc);
  };

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Diagnostic Trouble Codes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-red-500">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Failed to load DTC data</p>
            <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-2">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader className={compact ? "pb-2" : ""}>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Diagnostic Trouble Codes
            </div>
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </CardTitle>
          {!compact && (
            <CardDescription>
              Active diagnostic trouble codes across all protocols
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Summary Stats */}
            {dtcData && !compact && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 rounded border">
                  <div className="text-2xl font-bold">{dtcData.total_count}</div>
                  <div className="text-xs text-muted-foreground">Total DTCs</div>
                </div>
                <div className="text-center p-3 rounded border">
                  <div className="text-2xl font-bold text-red-500">{dtcData.active_count}</div>
                  <div className="text-xs text-muted-foreground">Active</div>
                </div>
                <div className="text-center p-3 rounded border">
                  <div className="text-2xl font-bold text-orange-500">
                    {dtcData.by_severity.critical || 0}
                  </div>
                  <div className="text-xs text-muted-foreground">Critical</div>
                </div>
                <div className="text-center p-3 rounded border">
                  <div className="text-2xl font-bold text-blue-500">
                    {Object.keys(dtcData.by_protocol).length}
                  </div>
                  <div className="text-xs text-muted-foreground">Protocols</div>
                </div>
              </div>
            )}

            {/* Filters and Search */}
            {showFilters && (
              <div className="flex flex-col sm:flex-row gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search DTCs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={filters.severity || undefined} onValueChange={(value) =>
                  setFilters(prev => ({ ...prev, severity: value || undefined }))
                }>
                  <SelectTrigger className="w-full sm:w-32">
                    <SelectValue placeholder="Severity" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Severities</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={filters.protocol || undefined} onValueChange={(value) =>
                  setFilters(prev => ({ ...prev, protocol: value || undefined }))
                }>
                  <SelectTrigger className="w-full sm:w-32">
                    <SelectValue placeholder="Protocol" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Protocols</SelectItem>
                    <SelectItem value="rvc">RV-C</SelectItem>
                    <SelectItem value="j1939">J1939</SelectItem>
                    <SelectItem value="firefly">Firefly</SelectItem>
                    <SelectItem value="spartan_k2">Spartan K2</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* DTC Table */}
            <div className="rounded-md border" style={{ maxHeight, overflow: 'auto' }}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('code')}
                    >
                      <div className="flex items-center gap-1">
                        Code
                        {sortField === 'code' && (
                          sortDirection === 'asc' ? <SortAsc className="h-3 w-3" /> : <SortDesc className="h-3 w-3" />
                        )}
                      </div>
                    </TableHead>
                    <TableHead>Protocol</TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('system_type')}
                    >
                      <div className="flex items-center gap-1">
                        System
                        {sortField === 'system_type' && (
                          sortDirection === 'asc' ? <SortAsc className="h-3 w-3" /> : <SortDesc className="h-3 w-3" />
                        )}
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('severity')}
                    >
                      <div className="flex items-center gap-1">
                        Severity
                        {sortField === 'severity' && (
                          sortDirection === 'asc' ? <SortAsc className="h-3 w-3" /> : <SortDesc className="h-3 w-3" />
                        )}
                      </div>
                    </TableHead>
                    {!compact && <TableHead>Description</TableHead>}
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('count')}
                    >
                      <div className="flex items-center gap-1">
                        Count
                        {sortField === 'count' && (
                          sortDirection === 'asc' ? <SortAsc className="h-3 w-3" /> : <SortDesc className="h-3 w-3" />
                        )}
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('last_seen')}
                    >
                      <div className="flex items-center gap-1">
                        Last Seen
                        {sortField === 'last_seen' && (
                          sortDirection === 'asc' ? <SortAsc className="h-3 w-3" /> : <SortDesc className="h-3 w-3" />
                        )}
                      </div>
                    </TableHead>
                    {showActions && <TableHead>Actions</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    // Loading skeleton
                    [...Array(5)].map((_, i) => (
                      <TableRow key={i}>
                        <TableCell><div className="animate-pulse bg-gray-200 h-4 rounded w-16"></div></TableCell>
                        <TableCell><div className="animate-pulse bg-gray-200 h-4 rounded w-12"></div></TableCell>
                        <TableCell><div className="animate-pulse bg-gray-200 h-4 rounded w-20"></div></TableCell>
                        <TableCell><div className="animate-pulse bg-gray-200 h-4 rounded w-16"></div></TableCell>
                        {!compact && <TableCell><div className="animate-pulse bg-gray-200 h-4 rounded w-32"></div></TableCell>}
                        <TableCell><div className="animate-pulse bg-gray-200 h-4 rounded w-8"></div></TableCell>
                        <TableCell><div className="animate-pulse bg-gray-200 h-4 rounded w-16"></div></TableCell>
                        {showActions && <TableCell><div className="animate-pulse bg-gray-200 h-4 rounded w-20"></div></TableCell>}
                      </TableRow>
                    ))
                  ) : filteredAndSortedDTCs.length ? (
                    filteredAndSortedDTCs.map((dtc) => (
                      <TableRow
                        key={dtc.id}
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => handleDTCSelect(dtc)}
                      >
                        <TableCell className="font-mono">{dtc.code}</TableCell>
                        <TableCell>
                          <Badge className={getProtocolColor(dtc.protocol)}>
                            {dtc.protocol.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell className="capitalize">
                          {dtc.system_type.replace(/_/g, ' ')}
                        </TableCell>
                        <TableCell>
                          <Badge variant={getSeverityVariant(dtc.severity)}>
                            {dtc.severity}
                          </Badge>
                        </TableCell>
                        {!compact && (
                          <TableCell className="max-w-xs truncate">
                            {dtc.description}
                          </TableCell>
                        )}
                        <TableCell>{dtc.count}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(dtc.last_seen).toLocaleDateString()}
                        </TableCell>
                        {showActions && (
                          <TableCell onClick={(e) => e.stopPropagation()}>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDTCSelect(dtc)}
                              >
                                <Eye className="h-3 w-3" />
                              </Button>
                              {!dtc.resolved && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleResolveDTC(dtc)}
                                  disabled={resolveMutation.isPending}
                                >
                                  <CheckCircle className="h-3 w-3" />
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        )}
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={compact ? 7 : 8} className="h-24 text-center">
                        <div className="flex flex-col items-center gap-2 text-muted-foreground">
                          <Shield className="h-8 w-8" />
                          <p>No DTCs found</p>
                          {searchTerm && (
                            <Button variant="ghost" size="sm" onClick={() => setSearchTerm('')}>
                              Clear search
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* DTC Detail Dialog */}
      <DTCDetailDialog
        dtc={selectedDTC}
        isOpen={showDetailDialog}
        onClose={() => setShowDetailDialog(false)}
        onResolve={handleResolveDTC}
      />
    </>
  );
};

export default DTCManager;
