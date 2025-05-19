#!/usr/bin/env node
/**
 * Script to generate TypeScript types from the OpenAPI schema
 *
 * This script generates TypeScript types for the frontend based on the
 * backend's OpenAPI schema, ensuring type consistency between frontend and backend.
 *
 * Usage:
 *   npm run generate:api-types
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

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

// Ensure the output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  console.log(`Created output directory: ${OUTPUT_DIR}`);
}

// Check if the OpenAPI JSON file exists
if (!fs.existsSync(OPENAPI_JSON_PATH)) {
  console.error(`Error: OpenAPI schema not found at ${OPENAPI_JSON_PATH}`);
  console.error(
    "Please run \"poetry run python scripts/export_openapi.py\" first."
  );
  process.exit(1);
}

// Check if openapi-typescript is installed
try {
  execSync("npx openapi-typescript --version", { stdio: "ignore" });
} catch (error) {
  console.log("openapi-typescript is not installed. Installing...");

  try {
    execSync("npm install --save-dev openapi-typescript", { stdio: "inherit" });
    console.log("Successfully installed openapi-typescript");
  } catch (installError) {
    console.error("Error installing openapi-typescript:", installError.message);
    process.exit(1);
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

  // Add import to fix TypeScript interface parsing errors
  const typesContent = fs.readFileSync(TYPES_FILE, "utf8");
  const importStatement =
    "// Auto-generated TypeScript types from OpenAPI schema\n" +
    "// To regenerate, run: npm run generate:api-types\n\n" +
    "import { type } from \"os\"; // Import to fix TypeScript interface parsing errors\n\n";

  fs.writeFileSync(TYPES_FILE, importStatement + typesContent);
  console.log("Added import to fix TypeScript interface parsing errors");

  // Create an index.ts file that re-exports everything
  const indexContent =
    "// Re-export all generated types\nexport * from \"./types\";\n";
  fs.writeFileSync(path.join(OUTPUT_DIR, "index.ts"), indexContent);
  console.log("Created index.ts file for easy importing");
} catch (error) {
  console.error("Error generating TypeScript types:", error.message);
  process.exit(1);
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
    } catch (error) {
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

    console.log(
      `Successfully generated TypeScript API client in ${OUTPUT_DIR}/client`
    );
  } catch (error) {
    console.error("Error generating TypeScript API client:", error.message);
    console.error("API types were still generated successfully.");
  }
}

console.log("\nDone! TypeScript types are now in sync with the API.");
