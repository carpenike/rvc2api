/**
 * This file is used to test if the TypeScript configuration is working correctly.
 */

// Import something from the project to test imports
import { WS_URL } from "./utils/config";

// Define a simple test function
export function testConfiguration(): string {
  return `Configuration test is working. WS_URL: ${WS_URL}`;
}

// Define a simple interface to test TypeScript
export interface TestConfig {
  name: string;
  value: number;
  optional?: boolean;
}

// Create an object with the interface type
const config: TestConfig = {
  name: "test",
  value: 123
};

console.log(config);
