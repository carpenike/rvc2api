/* eslint-env node */
/** @type {import('jest').Config} */
module.exports = {
  // Use ESM-compatible ts-jest preset
  preset: "ts-jest/presets/js-with-ts-esm",
  testEnvironment: "jsdom",

  // Root directory for Jest
  roots: ["<rootDir>/src"],

  // File extensions to look for
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json"],

  // Test file patterns
  testMatch: ["**/__tests__/**/*.ts?(x)", "**/?(*.)+(spec|test).ts?(x)"],

  // Enable ESM support
  extensionsToTreatAsEsm: [".ts", ".tsx"],

  // Transform configuration with import.meta support
  transform: {
    "^.+\\.[tj]sx?$": [
      "ts-jest",
      {
        useESM: true,
        tsconfig: "tsconfig.test.json",
        astTransformers: {
          before: [
            {
              path: "ts-jest-mock-import-meta",
              options: {
                metaObjectReplacement: {
                  url: "https://localhost:3000",
                  env: {
                    VITE_API_BASE_URL: "http://localhost:8000",
                    VITE_WS_BASE_URL: "ws://localhost:8000",
                    MODE: "test",
                    BASE_URL: "/",
                    PROD: false,
                    DEV: false,
                    SSR: false,
                    NODE_ENV: "test"
                  }
                }
              }
            }
          ]
        }
      }
    ]
  },

  // Module name mapper for assets, styles, and ESM compatibility
  moduleNameMapper: {
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    "\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$":
      "<rootDir>/src/__mocks__/fileMock.js",
    "^(\\.{1,2}/.*)\\.js$": "$1"
  },

  // Transform ignore patterns - allow ESM modules to be transformed
  transformIgnorePatterns: [
    "node_modules/(?!(@testing-library|@tanstack|react-hot-toast|msw)/)"
  ],

  // Setup files
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],

  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/main.tsx",
    "!src/vite-env.d.ts",
    "!src/**/__tests__/**",
    "!src/**/*.test.{ts,tsx}",
    "!src/**/*.spec.{ts,tsx}",
    // Exclude files with import.meta.env until we get proper handling
    "!src/hooks/useEntities.ts",
    "!src/utils/config.ts"
  ],
  coverageDirectory: "coverage",
  coverageReporters: ["text", "lcov", "html"]
};
