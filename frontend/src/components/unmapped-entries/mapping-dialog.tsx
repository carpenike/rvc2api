/**
 * Mapping Dialog Component
 *
 * Provides a dialog interface for creating entity mappings from unmapped entries.
 */

import type { UnmappedEntry } from "@/api/types"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import React from "react"

import { zodResolver } from "@hookform/resolvers/zod"
import { IconLoader2 } from "@tabler/icons-react"
import { useForm } from "react-hook-form"
import { z } from "zod"

// Form validation schema
const mappingFormSchema = z.object({
  entity_id: z
    .string()
    .min(1, "Entity ID is required")
    .regex(/^[a-z0-9_]+$/, "Entity ID must contain only lowercase letters, numbers, and underscores"),
  friendly_name: z.string().min(1, "Friendly name is required"),
  device_type: z.string().min(1, "Device type is required"),
  suggested_area: z.string().optional(),
  capabilities: z.array(z.string()).optional(),
  notes: z.string().optional(),
})

type MappingFormData = z.infer<typeof mappingFormSchema>

interface MappingDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  unmappedEntry: UnmappedEntry | null
  onSubmit: (formData: MappingFormData) => Promise<void>
}

// Device type options with descriptions
const DEVICE_TYPES = [
  { value: "light", label: "Light", description: "Lighting control device" },
  { value: "lock", label: "Lock", description: "Door or compartment lock" },
  { value: "tank", label: "Tank", description: "Fluid tank sensor" },
  { value: "thermostat", label: "Thermostat", description: "Temperature control" },
  { value: "fan", label: "Fan", description: "Ventilation fan" },
  { value: "pump", label: "Pump", description: "Water or fluid pump" },
  { value: "sensor", label: "Sensor", description: "Generic sensor device" },
  { value: "switch", label: "Switch", description: "Generic switch control" },
  { value: "unknown", label: "Unknown", description: "Unknown device type" },
]

// Capability options by device type
const CAPABILITIES_BY_TYPE: Record<string, string[]> = {
  light: ["on_off", "brightness", "dimming"],
  lock: ["lock_unlock"],
  tank: ["level", "temperature"],
  thermostat: ["heating", "cooling", "temperature_control"],
  fan: ["on_off", "speed_control"],
  pump: ["on_off", "pressure_control"],
  sensor: ["temperature", "humidity", "pressure"],
  switch: ["on_off"],
  unknown: [],
}

export function MappingDialog({ open, onOpenChange, unmappedEntry, onSubmit }: MappingDialogProps) {
  const form = useForm<MappingFormData>({
    resolver: zodResolver(mappingFormSchema),
    defaultValues: {
      entity_id: "",
      friendly_name: "",
      device_type: "",
      suggested_area: "",
      capabilities: [],
      notes: "",
    },
  })

  const selectedDeviceType = form.watch("device_type")

  // Reset form when entry changes
  React.useEffect(() => {
    if (unmappedEntry && open) {
      const suggestedEntityId = generateEntityId(unmappedEntry)
      const suggestedFriendlyName = generateFriendlyName(unmappedEntry)

      form.reset({
        entity_id: suggestedEntityId,
        friendly_name: suggestedFriendlyName,
        device_type: unmappedEntry.suggestions?.[0]?.toLowerCase().includes("light") ? "light" : "",
        suggested_area: "",
        capabilities: [],
        notes: `Mapped from unmapped entry: PGN ${unmappedEntry.pgn_hex}, DGN ${unmappedEntry.dgn_hex}, Instance ${unmappedEntry.instance}`,
      })
    }
  }, [unmappedEntry, open, form])

  // Update capabilities when device type changes
  React.useEffect(() => {
    if (selectedDeviceType) {
      const defaultCapabilities = CAPABILITIES_BY_TYPE[selectedDeviceType] || []
      form.setValue("capabilities", defaultCapabilities)
    }
  }, [selectedDeviceType, form])

  const handleSubmit = async (data: MappingFormData) => {
    try {
      await onSubmit(data)
      onOpenChange(false)
      form.reset()
    } catch (error) {
      console.error("Failed to create mapping:", error)
    }
  }

  if (!unmappedEntry) {
    return null
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Entity Mapping</DialogTitle>
          <DialogDescription>
            Create a new entity configuration for the unmapped DGN/instance pair below.
            This will add the device to your system for monitoring and control.
          </DialogDescription>
        </DialogHeader>

        {/* Unmapped Entry Info */}
        <div className="bg-muted/50 rounded-lg p-4 space-y-2">
          <h4 className="font-medium text-sm">Unmapped Entry Details</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">PGN:</span> {unmappedEntry.pgn_hex}
              {unmappedEntry.pgn_name && (
                <span className="text-muted-foreground ml-1">({unmappedEntry.pgn_name})</span>
              )}
            </div>
            <div>
              <span className="font-medium">DGN:</span> {unmappedEntry.dgn_hex}
              {unmappedEntry.dgn_name && (
                <span className="text-muted-foreground ml-1">({unmappedEntry.dgn_name})</span>
              )}
            </div>
            <div>
              <span className="font-medium">Instance:</span> {unmappedEntry.instance}
            </div>
            <div>
              <span className="font-medium">Count:</span> {unmappedEntry.count.toLocaleString()}
            </div>
          </div>
          {unmappedEntry.suggestions && unmappedEntry.suggestions.length > 0 && (
            <div>
              <span className="font-medium text-sm">Suggestions:</span>
              <div className="mt-1 space-y-1">
                {unmappedEntry.suggestions.map((suggestion, index) => (
                  <div key={index} className="text-sm text-muted-foreground">
                    • {suggestion}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            {/* Entity ID */}
            <FormField
              control={form.control}
              name="entity_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Entity ID</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="my_light_1" />
                  </FormControl>
                  <FormDescription>
                    Unique identifier for this entity. Use lowercase letters, numbers, and underscores only.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Friendly Name */}
            <FormField
              control={form.control}
              name="friendly_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Friendly Name</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="My Light 1" />
                  </FormControl>
                  <FormDescription>
                    Human-readable name that will be displayed in the interface.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              {/* Device Type */}
              <FormField
                control={form.control}
                name="device_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Device Type</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select device type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {DEVICE_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            <div>
                              <div className="font-medium">{type.label}</div>
                              <div className="text-xs text-muted-foreground">{type.description}</div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Suggested Area */}
              <FormField
                control={form.control}
                name="suggested_area"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Area (Optional)</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="Living Room" />
                    </FormControl>
                    <FormDescription>
                      Physical location or area where this device is located.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Capabilities */}
            {selectedDeviceType && CAPABILITIES_BY_TYPE[selectedDeviceType] && (
              <FormField
                control={form.control}
                name="capabilities"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Capabilities</FormLabel>
                    <FormDescription>
                      Device capabilities (automatically set based on device type, but can be customized).
                    </FormDescription>
                    <div className="space-y-2">
                      {CAPABILITIES_BY_TYPE[selectedDeviceType].map((capability) => (
                        <div key={capability} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={capability}
                            checked={field.value?.includes(capability)}
                            onChange={(e) => {
                              const current = field.value || []
                              if (e.target.checked) {
                                field.onChange([...current, capability])
                              } else {
                                field.onChange(current.filter((c) => c !== capability))
                              }
                            }}
                            className="rounded border border-input"
                          />
                          <label htmlFor={capability} className="text-sm">
                            {capability.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                          </label>
                        </div>
                      ))}
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {/* Notes */}
            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Notes (Optional)</FormLabel>
                  <FormControl>
                    <Textarea {...field} placeholder="Additional notes about this device..." rows={3} />
                  </FormControl>
                  <FormDescription>
                    Optional notes about this device or mapping.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={form.formState.isSubmitting}
                className="gap-2"
              >
                {form.formState.isSubmitting && <IconLoader2 className="h-4 w-4 animate-spin" />}
                Create Mapping
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Generate a suggested entity ID from unmapped entry
 */
function generateEntityId(entry: UnmappedEntry): string {
  const dgn = entry.dgn_hex.toLowerCase()
  const instance = entry.instance.replace(/[^a-z0-9]/gi, "")

  if (entry.dgn_name && entry.dgn_name !== "Unknown") {
    const name = entry.dgn_name
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "")
    return `${name}_${instance}`
  }

  return `unmapped_${dgn}_${instance}`
}

/**
 * Generate a suggested friendly name from unmapped entry
 */
function generateFriendlyName(entry: UnmappedEntry): string {
  if (entry.dgn_name && entry.dgn_name !== "Unknown") {
    return `${entry.dgn_name} (Instance ${entry.instance})`
  }

  return `Unmapped Device ${entry.dgn_hex} (Instance ${entry.instance})`
}
