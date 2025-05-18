// Jest configuration for React frontend
export default {
  // Root directory for Jest
  roots: ["<rootDir>/src"],

  // File extensions to look for
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json"],

  // Test environment
  testEnvironment: "jsdom",

  // Transform TS/TSX files with ts-jest
  transform: {
    "^.+\\.(ts|tsx)$": [
      "ts-jest",
      {
        useESM: true
      }
    ]
  },

  // Test file patterns
  testMatch: ["**/__tests__/**/*.ts?(x)", "**/?(*.)+(spec|test).ts?(x)"],

  // Module name mapper for assets and styles
  moduleNameMapper: {
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    "\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$":
      "<rootDir>/src/__mocks__/fileMock.js"
  },

  // Set up coverage collection
  collectCoverage: true,
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/main.tsx",
    "!src/vite-env.d.ts"
  ],
  coverageDirectory: "coverage",

  // Setup files
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"]
};
