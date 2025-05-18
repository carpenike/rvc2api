// ESLint Flat Config
import jsConfig from "@eslint/js";
import jsdoc from "eslint-plugin-jsdoc";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import tseslint from "typescript-eslint";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default [
  {
    ignores: [
      // Exclude all legacy web files in src/core_daemon (absolute from repo root)
      "src/core_daemon/web_ui/static/**",
      "src/core_daemon/web_ui/**/*.js",
      "src/core_daemon/web_ui/**/*.ts",
      "src/core_daemon/web_ui/**/*.tsx",
      "src/core_daemon/web_ui/**/*.jsx",
      // Exclude build and node_modules in web_ui
      "web_ui/dist/**",
      "web_ui/node_modules/**"
    ]
  },
  // Base JS config
  jsConfig.configs.recommended,

  // TypeScript configs
  ...tseslint.configs.recommended,

  // JavaScript common configs
  {
    files: ["**/*.{js,mjs}"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.es2020
      }
    },
    rules: {
      quotes: ["error", "double"],
      semi: ["error", "always"],
      "comma-dangle": ["error", "never"],
      "no-trailing-spaces": "error",
      "eol-last": ["error", "always"]
    }
  },

  // TypeScript specific configs
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.es2020
      },
      parser: tseslint.parser,
      parserOptions: {
        project: path.resolve(__dirname, "tsconfig.eslint.json"),
        tsconfigRootDir: __dirname
      }
    },
    // Only add plugins not already included by ...tseslint.configs.recommended
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      jsdoc: jsdoc
    },
    rules: {
      // TypeScript-specific rules
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": [
        "warn",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_"
        }
      ],

      // General formatting rules
      quotes: ["error", "double"],
      semi: ["error", "always"],
      "comma-dangle": ["error", "never"],
      "no-trailing-spaces": "error",
      "eol-last": ["error", "always"],

      // React-specific rules
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        {
          allowConstantExport: true
        }
      ],

      // JSDoc rules
      "jsdoc/require-jsdoc": "off",
      "jsdoc/check-alignment": "warn",
      "jsdoc/check-param-names": "warn",
      "jsdoc/check-tag-names": "warn",
      "jsdoc/check-types": "warn"
    }
  },

  // Node.js environment override for jest.setup.js
  {
    files: ["jest.setup.js"],
    languageOptions: {
      env: { node: true }
    }
  },

  // Test files
  {
    files: [
      "**/__tests__/**/*.{ts,tsx}",
      "**/*.test.{ts,tsx}",
      "**/*.spec.{ts,tsx}"
    ],
    languageOptions: {
      globals: {
        ...globals.jest
      }
    },
    rules: {
      // Relax rules for test files
      "@typescript-eslint/no-explicit-any": "off"
    }
  }
];
