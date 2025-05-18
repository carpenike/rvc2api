import { useState, useEffect } from "react";
import { Card, Toggle, Button, Alert, Badge } from "../components";
import { fetchLights, setLightState, setAllLights } from "../api/endpoints";

/**
 * Light interface defining the structure of a light device
 */
interface Light {
  /** Unique identifier for the light */
  id: string;

  /** Display name for the light */
  name: string;

  /** Current state of the light (on/off) */
  state: boolean;

  /** Type of light (e.g., 'interior', 'exterior') */
  type?: string;

  /** Physical location of the light in the RV */
  location?: string;

  /** Brightness level from 0-100 if supported */
  brightness?: number;

  /** Color value if the light supports color changes */
  color?: string;
}

/**
 * Lights page component
 *
 * Displays and controls the RV lighting system, allowing users to
 * view the status of lights and toggle them individually or in groups.
 * Lights are organized by location for easier management.
 *
 * @returns The Lights page component
 */
export function Lights() {
  /** List of all lights from the API */
  const [lights, setLights] = useState<Light[]>([]);

  /** Loading state for the API call */
  const [loading, setLoading] = useState(false);

  /** Error state for failed API calls */
  const [error, setError] = useState<string | null>(null);

  /** Lights organized by location for grouped display */
  const [groupedLights, setGroupedLights] = useState<Record<string, Light[]>>({});

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchLights()
      .then((data) => {
        setLights(data);
        // Group lights by location for better organization
        const grouped = data.reduce((acc: Record<string, Light[]>, light: Light) => {
          const location = light.location || "Unknown";
          if (!acc[location]) {
            acc[location] = [];
          }
          acc[location].push(light);
          return acc;
        }, {});
        setGroupedLights(grouped);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  /**
   * Handles toggling an individual light on or off
   *
   * @param lightId - The ID of the light to toggle
   * @param isOn - The new state to set (true for on, false for off)
   */
  const handleToggleLight = (lightId: string, isOn: boolean) => {
    // Update local state immediately for responsive UI
    setLights(prevLights =>
      prevLights.map(light =>
        light.id === lightId ? { ...light, state: isOn } : light
      )
    );

    // Also update the grouped lights
    setGroupedLights(prev => {
      const newGrouped = { ...prev };
      Object.keys(newGrouped).forEach(location => {
        newGrouped[location] = newGrouped[location].map(light =>
          light.id === lightId ? { ...light, state: isOn } : light
        );
      });
      return newGrouped;
    });

    // Send API request to update light state
    setLightState(lightId, isOn).catch((err: Error) => {
      console.error("Failed to update light state:", err);
      setError(`Failed to update ${lightId}: ${err.message}`);

      // Revert the state change if the API call fails
      setLights(prevLights =>
        prevLights.map(light =>
          light.id === lightId ? { ...light, state: !isOn } : light
        )
      );
    });
  };

  /**
   * Handles toggling all lights on or off
   *
   * @param state - The new state to set for all lights (true for on, false for off)
   */
  /**
   * Handles toggling all lights on or off
   *
   * @param state - The new state to set for all lights (true for on, false for off)
   */
  const handleToggleAllLights = (state: boolean) => {
    setAllLights(state)
      .then(() => {
        // Update all lights in state
        setLights(prevLights =>
          prevLights.map(light => ({ ...light, state }))
        );

        // Update grouped lights
        setGroupedLights(prev => {
          const newGrouped = { ...prev };
          Object.keys(newGrouped).forEach(location => {
            newGrouped[location] = newGrouped[location].map(light =>
              ({ ...light, state })
            );
          });
          return newGrouped;
        });
      })
      .catch((err: Error) => {
        console.error("Failed to update all lights:", err);
        setError(`Failed to update all lights: ${err.message}`);
      });
  };

  if (loading) {
    return (
      <section>
        <h1 className="text-3xl font-bold mb-6">RV-C Lights</h1>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-rv-primary"></div>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section>
        <h1 className="text-3xl font-bold mb-6">RV-C Lights</h1>
        <Alert
          variant="error"
          title="Error Loading Lights"
          onDismiss={() => setError(null)}
        >
          {error}
        </Alert>
      </section>
    );
  }

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-3xl font-bold">RV-C Lights</h1>

        <div className="flex space-x-2">
          <Button
            variant="primary"
            onClick={() => handleToggleAllLights(true)}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            All Lights On
          </Button>
          <Button
            variant="ghost"
            onClick={() => handleToggleAllLights(false)}
          >
            All Lights Off
          </Button>
        </div>
      </div>

      {/* Error notification */}
      {error && (
        <Alert
          variant="error"
          title="Error"
          className="mb-4"
          onDismiss={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {lights.length === 0 ? (
        <Card>
          <div className="p-8 text-center">
            <svg className="w-16 h-16 mx-auto text-rv-text/30 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <p className="text-rv-text/70">No lights found in the system.</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Lights Summary */}
          <Card className="mb-4">
            <div className="flex flex-wrap items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Lights Overview</h3>
                <p className="text-rv-text/70">
                  {lights.filter(l => l.state).length} of {lights.length} lights are currently on
                </p>
              </div>
              <div className="flex flex-wrap gap-2 mt-2 md:mt-0">
                {Object.keys(groupedLights).map(location => (
                  <Badge
                    key={location}
                    variant="primary"
                    className="px-3 py-1"
                  >
                    {location}: {groupedLights[location].filter(l => l.state).length}/{groupedLights[location].length}
                  </Badge>
                ))}
              </div>
            </div>
          </Card>

          {/* Lights grouped by location */}
          {Object.entries(groupedLights).map(([location, locationLights]) => (
            <Card
              key={location}
              title={
                <div className="flex justify-between items-center">
                  <span>{location}</span>
                  <div className="flex space-x-2">
                    <Button
                      variant="secondary"
                      className="py-1 px-3 text-sm"
                      onClick={() => locationLights.forEach(light => handleToggleLight(light.id, true))}
                    >
                      All On
                    </Button>
                    <Button
                      variant="ghost"
                      className="py-1 px-3 text-sm"
                      onClick={() => locationLights.forEach(light => handleToggleLight(light.id, false))}
                    >
                      All Off
                    </Button>
                  </div>
                </div>
              }
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {locationLights.map((light) => (
                  <div
                    key={light.id}
                    className={`relative bg-rv-surface/50 p-4 rounded-xl flex items-center justify-between light-card ${
                      light.state ? "on" : ""
                    }`}
                  >
                    <div className="flex flex-col">
                      <span className="font-medium">{light.name || light.id}</span>
                      {light.type && (
                        <span className="text-xs text-rv-text/70">{light.type}</span>
                      )}
                    </div>
                    <Toggle
                      isOn={light.state}
                      onToggle={(isOn) => handleToggleLight(light.id, isOn)}
                      size="md"
                    />
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
