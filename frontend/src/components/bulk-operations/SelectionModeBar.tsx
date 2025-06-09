/**
 * Selection Mode Bar Component
 *
 * Floating action bar that appears when devices are selected.
 * Provides quick access to bulk operations and group management.
 */

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Slider } from "@/components/ui/slider"
import { useQuickActions } from "@/hooks/useBulkOperations"
import {
    IconBulb,
    IconCheck,
    IconPower,
    IconRefresh,
    IconUsers,
    IconX
} from "@tabler/icons-react"
import { useState } from "react"
import { BulkOperationProgress } from "./BulkOperationProgress"
import { CreateGroupDialog } from "./CreateGroupDialog"

interface SelectionModeBarProps {
  selectedDevices: string[]
  onClearSelection: () => void
  onExitSelection: () => void
}

export function SelectionModeBar({
  selectedDevices,
  onClearSelection,
  onExitSelection
}: SelectionModeBarProps) {
  const [showCreateGroup, setShowCreateGroup] = useState(false)
  const [showBrightnessControl, setShowBrightnessControl] = useState(false)
  const [brightness, setBrightness] = useState([50])
  const [activeOperationId, setActiveOperationId] = useState<string | null>(null)

  const { allOff, systemCheck, setBrightness: setBulkBrightness, isLoading } = useQuickActions()

  if (selectedDevices.length === 0) return null

  const handleAllOff = async () => {
    try {
      const result = await allOff(selectedDevices)
      if (result?.operation_id) {
        setActiveOperationId(result.operation_id)
      }
    } catch (error) {
      console.error("Error executing All Off:", error)
    }
  }

  const handleSystemCheck = async () => {
    try {
      const result = await systemCheck(selectedDevices)
      if (result?.operation_id) {
        setActiveOperationId(result.operation_id)
      }
    } catch (error) {
      console.error("Error executing System Check:", error)
    }
  }

  const handleSetBrightness = async () => {
    try {
      const result = await setBulkBrightness(selectedDevices, brightness[0])
      if (result?.operation_id) {
        setActiveOperationId(result.operation_id)
      }
      setShowBrightnessControl(false)
    } catch (error) {
      console.error("Error setting brightness:", error)
    }
  }

  return (
    <>
      {/* Selection Mode Bar */}
      <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50">
        <div className="bg-background border rounded-lg shadow-lg p-4 min-w-96">
          <div className="flex items-center justify-between gap-4">
            {/* Selection Count */}
            <div className="flex items-center gap-2">
              <Badge variant="default" className="gap-1">
                <IconCheck className="h-3 w-3" />
                {selectedDevices.length} selected
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearSelection}
                className="h-6 px-2"
              >
                Clear
              </Button>
            </div>

            <Separator orientation="vertical" className="h-6" />

            {/* Quick Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleAllOff}
                disabled={isLoading}
                className="gap-2"
              >
                <IconPower className="h-4 w-4" />
                All Off
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={handleSystemCheck}
                disabled={isLoading}
                className="gap-2"
              >
                <IconRefresh className="h-4 w-4" />
                Check Status
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowBrightnessControl(!showBrightnessControl)}
                className="gap-2"
              >
                <IconBulb className="h-4 w-4" />
                Brightness
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreateGroup(true)}
                className="gap-2"
              >
                <IconUsers className="h-4 w-4" />
                Save Group
              </Button>
            </div>

            <Separator orientation="vertical" className="h-6" />

            {/* Exit Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onExitSelection}
              className="gap-2"
            >
              <IconX className="h-4 w-4" />
              Done
            </Button>
          </div>

          {/* Brightness Control */}
          {showBrightnessControl && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium min-w-0">
                  Brightness: {brightness[0]}%
                </span>
                <div className="flex-1">
                  <Slider
                    value={brightness}
                    onValueChange={setBrightness}
                    max={100}
                    step={5}
                    className="w-full"
                  />
                </div>
                <Button
                  size="sm"
                  onClick={handleSetBrightness}
                  disabled={isLoading}
                >
                  Apply
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowBrightnessControl(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Group Dialog */}
      <CreateGroupDialog
        open={showCreateGroup}
        onOpenChange={setShowCreateGroup}
        selectedDevices={selectedDevices}
        onGroupCreated={() => {
          setShowCreateGroup(false)
          onExitSelection() // Exit selection mode after creating group
        }}
      />

      {/* Bulk Operation Progress */}
      {activeOperationId && (
        <BulkOperationProgress
          operationId={activeOperationId}
          onComplete={() => setActiveOperationId(null)}
        />
      )}
    </>
  )
}
