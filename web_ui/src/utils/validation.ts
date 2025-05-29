import { z } from "zod";

// Example: Entity control command schema
export const EntityControlCommandSchema = z.object({
  command: z.string(),
  state: z.union([z.string(), z.boolean()]).optional(),
  brightness: z.number().min(0).max(100).optional()
});

export type EntityControlCommand = z.infer<typeof EntityControlCommandSchema>;

// Add more schemas as needed for API requests/responses
