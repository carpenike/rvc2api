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
      // Exclude build and node_modules (both relative and absolute paths)
      "dist/**",
      "dist-ssr/**",
      "node_modules/**",
      ".vite/**",
      ".vite-temp/**",
      "web_ui/dist/**",
      "web_ui/dist-ssr/**",
      "web_ui/node_modules/**",
      "web_ui/.vite/**",
      "web_ui/.vite-temp/**",
      "web_ui/node_modules/.vite/**",
      // Exclude any other output/cache directories
      "web_ui/**/*.tsbuildinfo",
      "web_ui/**/*.log",
      "web_ui/.cache/**",
      // Exclude documentation and generated output
      "web_ui/site/**",
      "web_ui/docs/_build/**",
      "web_ui/assets/javascripts/workers/*.min.js",
      "web_ui/CNAME",
      "web_ui/objects.inv",
      "web_ui/sitemap.xml*",
      "web_ui/index.html",
      "web_ui/404.html",
      // Exclude Node.js scripts (not frontend source)
      "web_ui/scripts/**",
      // Exclude global cache, build, and virtualenv directories
      "**/.venv/**",
      "**/venv/**",
      "**/.env/**",
      "**/.cache/**",
      "**/.mypy_cache/**",
      "**/.pytest_cache/**",
      "**/.ruff_cache/**",
      "**/.tox/**",
      "**/.nox/**",
      "**/.eggs/**",
      "**/.idea/**",
      "**/.vscode/**",
      "**/.devcontainer/**",
      "**/devcontainer/**",
      "**/.devcontainer/home-cache/**",
      "**/lib/**",
      "**/bin/**",
      "**/site-packages/**",
      "**/usr/**",
      "**/opt/**",
      "**/lib64/**",
      "**/include/**",
      "**/share/**",
      "**/pyvenv.cfg",
      "**/*.pyc",
      "**/*.pyo",
      "**/__pycache__/**",
      "**/virtualenv/**",
      "**/env/**",
      "**/ENV/**",
      "**/build/**",
      "**/tmp/**",
      "**/temp/**",
      "**/log/**",
      "**/logs/**",
      "**/output/**",
      "**/coverage/**",
      "**/.history/**",
      "**/.DS_Store",
      "**/Thumbs.db",
      "**/desktop.ini",
      "**/npm-debug.log",
      "**/yarn-error.log",
      "**/pnpm-debug.log",
      "**/pip-log.txt",
      "**/pip-delete-this-directory.txt"
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

  // shadcn/UI components override - suppress React refresh warnings
  {
    files: ["**/components/ui/*.{ts,tsx}"],
    rules: {
      "react-refresh/only-export-components": "off"
    }
  },

  // Node.js environment override for jest.setup.js
  {
    files: ["jest.setup.js"],
    languageOptions: {
      env: { node: true }
    }
  },

  // CommonJS configuration files
  {
    files: ["jest.config.cjs", "src/__mocks__/fileMock.js"],
    languageOptions: {
      globals: {
        ...globals.node
      },
      sourceType: "script"
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
