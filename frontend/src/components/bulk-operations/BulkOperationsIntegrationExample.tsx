/**
 * Bulk Operations Integration Example
 *
 * Example component demonstrating how to integrate the new V2 bulk operations
 * components with existing entity pages and workflows.
 */

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useEntitiesV2 } from "@/hooks/domains/useEntitiesV2";
import { useState } from "react";
import { BulkOperationsModalV2 } from "./BulkOperationsModalV2";
import { IconChecks, IconLoader } from "@tabler/icons-react";

interface BulkOperationsIntegrationExampleProps {
  /** Optional pre-selected entity IDs */
  preSelectedEntities?: string[];
  /** Page context for analytics */
  pageContext?: string;
}

export function BulkOperationsIntegrationExample({
  preSelectedEntities = [],
  pageContext = "entities"
}: BulkOperationsIntegrationExampleProps) {
  const [showBulkModal, setShowBulkModal] = useState(false);

  // Fetch entities for the modal
  const { data: entityCollection, isLoading } = useEntitiesV2();
  const entities = entityCollection?.entities || [];

  // Convert entities array to lookup object for display names
  const entitiesLookup = entities.reduce((acc, entity) => {
    acc[entity.entity_id] = {
      ...entity, // Include all properties first
      friendly_name: entity.name, // Add friendly_name for compatibility
    };
    return acc;
  }, {} as Record<string, { entity_id: string; name?: string; friendly_name?: string; [key: string]: unknown }>);

  const handleOpenBulkOperations = () => {
    setShowBulkModal(true);
  };


  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-8">
          <IconLoader className="h-6 w-6 animate-spin" />
          <span className="ml-2">Loading entities...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconChecks className="h-5 w-5" />
            Bulk Operations
          </CardTitle>
          <CardDescription>
            Perform operations on multiple entities simultaneously with real-time progress tracking
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground">
            {entities.length} entities available for bulk operations
          </div>

          {preSelectedEntities.length > 0 && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                {preSelectedEntities.length} entities pre-selected from {pageContext}
              </p>
            </div>
          )}

          <Button
            onClick={handleOpenBulkOperations}
            className="w-full"
            disabled={entities.length === 0}
          >
            Open Bulk Operations
          </Button>

          <div className="text-xs text-muted-foreground space-y-1">
            <p>• Select multiple entities with filtering and grouping</p>
            <p>• Execute power control, brightness, and toggle operations</p>
            <p>• Real-time progress tracking with error handling</p>
            <p>• Retry failed operations with detailed results</p>
          </div>
        </CardContent>
      </Card>

      {/* Bulk Operations Modal */}
      <BulkOperationsModalV2
        open={showBulkModal}
        onOpenChange={setShowBulkModal}
        initialSelection={preSelectedEntities}
        entities={entitiesLookup}
      />
    </>
  );
}

/**
 * Hook for integrating bulk operations into existing entity lists
 */
export function useBulkOperationsIntegration() {
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [selectedEntities, setSelectedEntities] = useState<string[]>([]);

  const openBulkOperations = (entityIds: string[] = []) => {
    setSelectedEntities(entityIds);
    setShowBulkModal(true);
  };

  const closeBulkOperations = () => {
    setShowBulkModal(false);
    setSelectedEntities([]);
  };

  return {
    showBulkModal,
    selectedEntities,
    openBulkOperations,
    closeBulkOperations
  };
}
