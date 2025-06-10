/**
 * Smart Manual Card - Tier 1 Vector Search Implementation
 *
 * Provides contextual help and "smart manual" functionality for DTCs.
 * Shows relevant troubleshooting steps, common causes, and solutions.
 *
 * This is a simplified implementation that provides immediate value
 * without requiring full vector search infrastructure.
 */

import type { DiagnosticTroubleCode } from "@/api/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import {
  IconBook,
  IconBulb,
  IconExternalLink,
  IconSearch,
  IconTool,
  IconX
} from "@tabler/icons-react"
import { useState } from "react"

interface TroubleshootingGuide {
  title: string
  description: string
  commonCauses: string[]
  immediateSteps: string[]
  toolsNeeded?: string[]
  safetyWarning?: string
  estimatedTime?: string
  skillLevel: "Beginner" | "Intermediate" | "Advanced" | "Professional"
}

/**
 * Smart manual database - contextual help for common RV systems
 */
const TROUBLESHOOTING_GUIDES: Record<string, TroubleshootingGuide> = {
  // Engine System Issues
  "engine_temperature": {
    title: "Engine Overheating",
    description: "Engine temperature is higher than normal operating range",
    commonCauses: [
      "Low coolant level",
      "Faulty thermostat",
      "Blocked radiator",
      "Water pump failure",
      "Blown head gasket"
    ],
    immediateSteps: [
      "Safely pull over and turn off engine immediately",
      "Let engine cool for 30+ minutes before checking",
      "Check coolant level when cool (never open hot radiator)",
      "Look for visible leaks under the vehicle",
      "Check radiator for debris or blockages"
    ],
    toolsNeeded: ["Flashlight", "Work gloves", "Coolant (if needed)"],
    safetyWarning: "Never remove radiator cap when engine is hot - risk of severe burns",
    estimatedTime: "15-30 minutes inspection",
    skillLevel: "Beginner"
  },

  "engine_oil": {
    title: "Engine Oil Pressure",
    description: "Low engine oil pressure detected",
    commonCauses: [
      "Low oil level",
      "Wrong oil viscosity",
      "Worn oil pump",
      "Clogged oil filter",
      "Engine bearing wear"
    ],
    immediateSteps: [
      "Stop driving immediately - severe engine damage risk",
      "Check oil level with dipstick",
      "Look for oil leaks under vehicle",
      "Check oil color and consistency",
      "If oil is low, add appropriate oil type"
    ],
    toolsNeeded: ["Dipstick", "Engine oil", "Funnel", "Work gloves"],
    safetyWarning: "Continued driving with low oil pressure will destroy engine",
    estimatedTime: "10-15 minutes",
    skillLevel: "Beginner"
  },

  // Electrical System Issues
  "power_voltage": {
    title: "Electrical Voltage Issue",
    description: "Battery or charging system voltage problem",
    commonCauses: [
      "Weak or failing battery",
      "Faulty alternator",
      "Loose connections",
      "Parasitic drain",
      "Overloaded circuits"
    ],
    immediateSteps: [
      "Check battery voltage with multimeter (should be 12.6V+)",
      "Inspect battery terminals for corrosion",
      "Test alternator output while running (13.5-14.5V)",
      "Check for loose or corroded connections",
      "Look for signs of overheated wiring"
    ],
    toolsNeeded: ["Multimeter", "Wire brush", "Battery terminal cleaner", "Work gloves"],
    estimatedTime: "20-30 minutes",
    skillLevel: "Intermediate"
  },

  // Climate System Issues
  "climate_hvac": {
    title: "HVAC System Issue",
    description: "Heating, ventilation, or air conditioning problem",
    commonCauses: [
      "Dirty air filter",
      "Low refrigerant",
      "Faulty thermostat",
      "Blocked ducts",
      "Compressor failure"
    ],
    immediateSteps: [
      "Check and replace air filter if dirty",
      "Verify thermostat settings and battery",
      "Check for blocked vents or returns",
      "Listen for unusual noises from unit",
      "Check circuit breakers and fuses"
    ],
    toolsNeeded: ["New air filter", "Screwdriver", "Flashlight"],
    estimatedTime: "15-45 minutes",
    skillLevel: "Beginner"
  },

  // Lighting System Issues
  "lighting": {
    title: "Lighting System Problem",
    description: "Issues with interior or exterior lighting",
    commonCauses: [
      "Burned out bulbs",
      "Blown fuses",
      "Loose connections",
      "Switch failure",
      "Wiring damage"
    ],
    immediateSteps: [
      "Check if multiple lights are affected (indicates fuse issue)",
      "Replace suspected burned-out bulbs",
      "Check relevant fuses in fuse box",
      "Test light switches for proper operation",
      "Inspect visible wiring for damage"
    ],
    toolsNeeded: ["Replacement bulbs", "Fuses", "Test light or multimeter"],
    estimatedTime: "10-20 minutes",
    skillLevel: "Beginner"
  },

  // Water System Issues
  "water_tank": {
    title: "Water System Issue",
    description: "Problem with water tanks, pump, or plumbing",
    commonCauses: [
      "Empty water tank",
      "Faulty water pump",
      "Clogged filters",
      "Frozen pipes",
      "Leak in system"
    ],
    immediateSteps: [
      "Check fresh water tank level",
      "Verify water pump is running when faucet opened",
      "Check for leaks under RV and in compartments",
      "Test water pressure at multiple faucets",
      "Check water pump fuse and connections"
    ],
    toolsNeeded: ["Flashlight", "Basic tools", "Water pump fuse"],
    estimatedTime: "15-30 minutes",
    skillLevel: "Beginner"
  }
}

/**
 * Get troubleshooting guide based on DTC information
 */
function getTroubleshootingGuide(dtc: DiagnosticTroubleCode): TroubleshootingGuide | null {
  const system = dtc.system_type.toLowerCase()
  const description = dtc.description.toLowerCase()
  const code = dtc.code.toLowerCase()

  // Match based on system and common patterns
  if (system.includes('engine')) {
    if (description.includes('temperature') || code.includes('temp')) {
      return TROUBLESHOOTING_GUIDES.engine_temperature ?? null
    }
    if (description.includes('oil') || description.includes('pressure')) {
      return TROUBLESHOOTING_GUIDES.engine_oil ?? null
    }
  }

  if (system.includes('power') || system.includes('electrical')) {
    return TROUBLESHOOTING_GUIDES.power_voltage ?? null
  }

  if (system.includes('climate') || system.includes('hvac')) {
    return TROUBLESHOOTING_GUIDES.climate_hvac ?? null
  }

  if (system.includes('lighting')) {
    return TROUBLESHOOTING_GUIDES.lighting ?? null
  }

  if (system.includes('water') || system.includes('tank')) {
    return TROUBLESHOOTING_GUIDES.water_tank ?? null
  }

  return null
}

/**
 * Search functionality for manual topics
 */
function searchTroubleshootingGuides(query: string): TroubleshootingGuide[] {
  if (!query || query.length < 2) return []

  const searchTerm = query.toLowerCase()
  const results: TroubleshootingGuide[] = []

  Object.values(TROUBLESHOOTING_GUIDES).forEach(guide => {
    const matches =
      guide.title.toLowerCase().includes(searchTerm) ||
      guide.description.toLowerCase().includes(searchTerm) ||
      guide.commonCauses.some(cause => cause.toLowerCase().includes(searchTerm))

    if (matches) {
      results.push(guide)
    }
  })

  return results
}

/**
 * Skill Level Badge Component
 */
function SkillLevelBadge({ level }: { level: string }) {
  const variants = {
    "Beginner": { variant: "default" as const, color: "text-green-700" },
    "Intermediate": { variant: "secondary" as const, color: "text-blue-700" },
    "Advanced": { variant: "secondary" as const, color: "text-amber-700" },
    "Professional": { variant: "destructive" as const, color: "text-red-700" }
  }

  const config = variants[level as keyof typeof variants] || variants.Beginner

  return (
    <Badge variant={config.variant} className="gap-1">
      <IconTool className="h-3 w-3" />
      {level}
    </Badge>
  )
}

/**
 * Troubleshooting Guide Display Component
 */
function TroubleshootingGuideDisplay({ guide }: { guide: TroubleshootingGuide }) {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold">{guide.title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{guide.description}</p>
        </div>
        <div className="flex gap-2">
          <SkillLevelBadge level={guide.skillLevel} />
          {guide.estimatedTime && (
            <Badge variant="outline" className="text-xs">
              {guide.estimatedTime}
            </Badge>
          )}
        </div>
      </div>

      {guide.safetyWarning && (
        <div className="p-3 rounded-lg border border-red-200 bg-red-50">
          <div className="flex items-start gap-2">
            <IconX className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-red-900">Safety Warning</p>
              <p className="text-sm text-red-800 mt-1">{guide.safetyWarning}</p>
            </div>
          </div>
        </div>
      )}

      <div>
        <h4 className="text-sm font-medium mb-2">Common Causes</h4>
        <ul className="space-y-1 text-sm text-muted-foreground">
          {guide.commonCauses.map((cause, index) => (
            <li key={index} className="flex items-start gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-muted-foreground mt-2 flex-shrink-0" />
              {cause}
            </li>
          ))}
        </ul>
      </div>

      <Separator />

      <div>
        <h4 className="text-sm font-medium mb-2">Immediate Steps</h4>
        <ol className="space-y-2 text-sm">
          {guide.immediateSteps.map((step, index) => (
            <li key={index} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center font-medium">
                {index + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>

      {guide.toolsNeeded && guide.toolsNeeded.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Tools Needed</h4>
          <div className="flex flex-wrap gap-1">
            {guide.toolsNeeded.map((tool, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {tool}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Smart Manual Card Component
 */
interface SmartManualCardProps {
  activeDTC?: DiagnosticTroubleCode
}

export default function SmartManualCard({ activeDTC }: SmartManualCardProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [isSearching, setIsSearching] = useState(false)

  // Get contextual guide for active DTC
  const contextualGuide = activeDTC ? getTroubleshootingGuide(activeDTC) : null

  // Get search results
  const searchResults = searchQuery ? searchTroubleshootingGuides(searchQuery) : []

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setIsSearching(true)
    // Simulate search delay for better UX
    setTimeout(() => setIsSearching(false), 300)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconBook className="size-5" />
          Smart Manual
        </CardTitle>
        <CardDescription>
          {activeDTC ? "Troubleshooting help for active issue" : "Search troubleshooting guides"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Search Interface */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <IconSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search troubleshooting guides..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit" disabled={isSearching} size="sm">
              {isSearching ? "Searching..." : "Search"}
            </Button>
          </form>

          {/* Contextual Help for Active DTC */}
          {contextualGuide && !searchQuery && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <IconBulb className="h-4 w-4 text-amber-500" />
                <span className="text-sm font-medium">Help for Current Issue</span>
              </div>
              <div className="border rounded-lg p-4">
                <TroubleshootingGuideDisplay guide={contextualGuide} />
              </div>
            </div>
          )}

          {/* Search Results */}
          {searchQuery && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium">
                  Search Results ({searchResults.length})
                </span>
                {searchResults.length === 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="gap-1 text-xs"
                    onClick={() => setSearchQuery("")}
                  >
                    <IconX className="h-3 w-3" />
                    Clear
                  </Button>
                )}
              </div>

              {isSearching ? (
                <div className="space-y-3">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <div key={i} className="border rounded-lg p-4">
                      <Skeleton className="h-4 w-3/4 mb-2" />
                      <Skeleton className="h-3 w-1/2 mb-3" />
                      <Skeleton className="h-16 w-full" />
                    </div>
                  ))}
                </div>
              ) : searchResults.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground">
                  <IconSearch className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No guides found for "{searchQuery}"</p>
                  <p className="text-xs mt-1">Try searching for: engine, electrical, water, climate, or lighting</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {searchResults.map((guide, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <TroubleshootingGuideDisplay guide={guide} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* No Active Issues and No Search */}
          {!contextualGuide && !searchQuery && (
            <div className="text-center py-6">
              <IconBook className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm font-medium">No Active Issues</p>
              <p className="text-xs text-muted-foreground mt-1">
                Search above for troubleshooting guides, or visit the Documentation page for the full RV-C manual
              </p>
              <Button asChild variant="ghost" size="sm" className="mt-2 gap-1">
                <a href="/documentation" className="gap-1">
                  <IconExternalLink className="h-3 w-3" />
                  View Full Documentation
                </a>
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
