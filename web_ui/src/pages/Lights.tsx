import { useEffect, useState } from "react";
import type { LightCommand } from "../api/endpoints";
import { fetchLights, setLightState } from "../api/endpoints";
import type { LightStatus } from "../api/types";
import { Alert, Badge, Card, Loading } from "../components";

// Backend entity type for lights (extends LightStatus with capabilities)
interface LightEntity extends LightStatus {
  capabilities?: string[];
  friendly_name?: string;
  suggested_area?: string;
  groups?: string[];
}

// Local Light type for UI
interface Light {
  id: string;
  name: string;
  state: "on" | "off";
  capabilities: string[];
  brightness?: number;
  location?: string;
  groups?: string[];
}

export function Lights() {
  const [groupedLights, setGroupedLights] = useState<Record<string, Light[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Map backend entity to Light type
  function mapEntityToLight(entity: LightEntity): Light {
    return {
      id: entity.id,
      name: entity.friendly_name || entity.name || entity.id,
      state: entity.state ? "on" : "off",
      capabilities: entity.capabilities ?? [],
      brightness: entity.brightness,
      location: entity.suggested_area || entity.location || "Unknown",
      groups: entity.groups || []
    };
  }

  // Fetch lights on mount
  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchLights()
      .then((data: LightStatus[]) => {
        // data is an array of entities, map to LightEntity and then to Light
        const lightsArr: Light[] = (data as LightEntity[]).map(mapEntityToLight);
        // Group by location
        const grouped = lightsArr.reduce((acc: Record<string, Light[]>, light: Light) => {
          const location = light.location || "Unknown";
          if (!acc[location]) acc[location] = [];
          acc[location].push(light);
          return acc;
        }, {});
        setGroupedLights(grouped);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Toggle a single light (with optional brightness)
  const handleToggle = (light: Light) => {
    const newState = light.state === "on" ? "off" : "on";
    const command: LightCommand = { command: "set", state: newState };
    if (light.capabilities.includes("brightness") && light.brightness !== undefined) {
      command.brightness = light.brightness;
    }
    setLightState(light.id, command)
      .then(() => {
        setGroupedLights((prev) => {
          const updated: Record<string, Light[]> = {};
          for (const [loc, lights] of Object.entries(prev)) {
            updated[loc] = lights.map((l) =>
              l.id === light.id ? { ...l, state: newState } : l
            );
          }
          return updated;
        });
      })
      .catch((e: Error) => setError(e.message));
  };

  // Handle brightness change
  const handleBrightnessChange = (light: Light, value: number) => {
    const command: LightCommand = { command: "set", state: "on", brightness: value };
    setLightState(light.id, command)
      .then(() => {
        setGroupedLights((prev) => {
          const updated: Record<string, Light[]> = {};
          for (const [loc, lights] of Object.entries(prev)) {
            updated[loc] = lights.map((l) =>
              l.id === light.id ? { ...l, brightness: value, state: "on" } : l
            );
          }
          return updated;
        });
      })
      .catch((e: Error) => setError(e.message));
  };

  if (loading) return <Loading />;
  if (error) return <Alert variant="error">{error}</Alert>;

  return (
    <div className="px-4 py-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Lights</h1>
      {Object.keys(groupedLights).length === 0 ? (
        <Alert variant="info">No lights found.</Alert>
      ) : (
        Object.entries(groupedLights).map(([location, lights]) => (
          <div key={location} className="mb-8">
            <h2 className="text-lg font-semibold mb-3">{location}</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {lights.map((light) => {
                const isOn = light.state === "on";
                const hasBrightness = light.capabilities.includes("brightness");
                return (
                  <div
                    key={light.id}
                    tabIndex={0}
                    role="button"
                    aria-pressed={isOn}
                    aria-label={`Toggle ${light.name}`}
                    onClick={() => handleToggle(light)}
                    onKeyDown={(e: React.KeyboardEvent<HTMLDivElement>) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleToggle(light);
                      }
                    }}
                    className="outline-none focus:ring-2 focus:ring-primary-400 dark:focus:ring-primary-600 rounded-xl"
                  >
                    <Card
                      className={`transition-all cursor-pointer select-none flex flex-col items-center p-6 border rounded-xl shadow-md
                        ${isOn
                          ? "bg-primary-100 dark:bg-primary-900 border-primary-400 dark:border-primary-700 shadow-lg scale-105"
                          : "bg-background dark:bg-background border-gray-200 dark:border-gray-700 shadow"
                        }
                      `}
                    >
                      <div className="flex items-center gap-2 mb-2 w-full justify-between">
                        <span className="font-medium text-lg">{light.name}</span>
                        {hasBrightness && (
                          <Badge variant="primary">Brightness</Badge>
                        )}
                      </div>
                      <div className="flex-1 flex flex-col items-center justify-center w-full">
                        <span className={`text-2xl font-bold ${isOn ? "text-primary-700 dark:text-primary-200" : "text-gray-400 dark:text-gray-500"}`}>{isOn ? "On" : "Off"}</span>
                        {hasBrightness && (
                          <div className="w-full mt-4">
                            <input
                              type="range"
                              min={0}
                              max={100}
                              value={light.brightness ?? 0}
                              onChange={(e) => handleBrightnessChange(light, Number(e.target.value))}
                              className="w-full accent-primary-500 h-2 rounded-lg appearance-none bg-primary-200 dark:bg-primary-800 focus:outline-none focus:ring-2 focus:ring-primary-400"
                              aria-label={`Set brightness for ${light.name}`}
                              style={{ zIndex: 1, position: "relative" }}
                            />
                            <div className="text-xs text-right mt-1 text-primary-700 dark:text-primary-200">{light.brightness ?? 0}%</div>
                          </div>
                        )}
                      </div>
                    </Card>
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default Lights;
