#!/usr/bin/env node
/* eslint-env node */

/* eslint-disable no-undef */
/**
 * Script to generate TypeScript types from the OpenAPI schema
 *
 * This script generates TypeScript types for the frontend based on the
 * backend's OpenAPI schema, ensuring type consistency between frontend and backend.
 *
 * Usage:
 *   npm run generate:api-types
 */

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const OPENAPI_JSON_PATH = path.join(
  __dirname,
  "..",
  "..",
  "docs",
  "api",
  "openapi.json"
);
const OUTPUT_DIR = path.join(__dirname, "..", "src", "api", "generated");
const TYPES_FILE = path.join(OUTPUT_DIR, "types.ts");

async function main() {
  // Ensure the output directory exists
  try {
    await fs.promises.mkdir(OUTPUT_DIR, { recursive: true });
  } catch (err) {
    console.error(`Error creating output directory: ${OUTPUT_DIR}`);
    console.error(err.message);
    process.exitCode = 1;
    return;
  }

  // Check if the OpenAPI JSON file exists
  if (!fs.existsSync(OPENAPI_JSON_PATH)) {
    console.error(`Error: OpenAPI schema not found at ${OPENAPI_JSON_PATH}`);
    console.error(
      "Please run \"poetry run python scripts/export_openapi.py\" first."
    );
    process.exitCode = 1;
    return;
  }

  // Check if openapi-typescript is installed
  try {
    execSync("npx openapi-typescript --version", { stdio: "ignore" });
  } catch {
    console.log("openapi-typescript is not installed. Installing...");
    try {
      execSync("npm install --save-dev openapi-typescript", { stdio: "inherit" });
      console.log("Successfully installed openapi-typescript");
    } catch (installError) {
      console.error("Error installing openapi-typescript:", installError.message);
      process.exitCode = 1;
      return;
    }
  }

  // Generate TypeScript types
  console.log("Generating TypeScript types from OpenAPI schema...");
  try {
    execSync(
      `npx openapi-typescript ${OPENAPI_JSON_PATH} --output ${TYPES_FILE}`,
      { stdio: "inherit" }
    );
    console.log(`Successfully generated TypeScript types at ${TYPES_FILE}`);
  } catch (error) {
    console.error("Error generating TypeScript types:", error.message);
    process.exitCode = 1;
    return;
  }

  // Add import to fix TypeScript interface parsing errors
  try {
    const typesContent = await fs.promises.readFile(TYPES_FILE, "utf8");
    const importStatement =
      "// Auto-generated TypeScript types from OpenAPI schema\n" +
      "// To regenerate, run: npm run generate:api-types\n\n" +
      "import type React from 'react'; // Import to fix TypeScript interface parsing errors\n\n";
    await fs.promises.writeFile(TYPES_FILE, importStatement + typesContent);
    console.log("Added import to fix TypeScript interface parsing errors");
  } catch (err) {
    console.error("Error updating types.ts with import statement:", err.message);
    process.exitCode = 1;
    return;
  }

  // Create an index.ts file that re-exports everything
  try {
    const indexContent =
      "// Re-export all generated types\nexport * from './types';\n";
    await fs.promises.writeFile(path.join(OUTPUT_DIR, "index.ts"), indexContent);
    console.log("Created index.ts file for easy importing");
  } catch (err) {
    console.error("Error creating index.ts:", err.message);
    process.exitCode = 1;
    return;
  }

  // Generate API client (optional)
  if (process.argv.includes("--client")) {
    console.log("\nGenerating TypeScript API client from OpenAPI schema...");
    try {
      // Check if OpenAPI Generator CLI is installed
      try {
        execSync("npx @openapitools/openapi-generator-cli version", {
          stdio: "ignore"
        });
      } catch {
        console.log(
          "@openapitools/openapi-generator-cli is not installed. Installing..."
        );
        execSync("npm install --save-dev @openapitools/openapi-generator-cli", {
          stdio: "inherit"
        });
      }
      // Generate the client
      execSync(
        `npx @openapitools/openapi-generator-cli generate -i ${OPENAPI_JSON_PATH} -g typescript-fetch -o ${OUTPUT_DIR}/client --additional-properties=typescriptThreePlus=true`,
        { stdio: "inherit" }
      );
      console.log("Successfully generated TypeScript API client.");
    } catch (error) {
      console.error("Error generating TypeScript API client:", error.message);
      process.exitCode = 1;
      return;
    }
  }

  console.log("\n✅ API types generation complete.");
}

main();
