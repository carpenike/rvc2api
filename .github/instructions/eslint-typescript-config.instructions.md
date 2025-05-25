---
applyTo: "**/web_ui/**"
---

# ESLint and TypeScript Configuration

> **Note**: This file focuses on ESLint/TypeScript configuration and troubleshooting. For TypeScript coding standards, best practices, and style guidelines, see [typescript-code-style.instructions.md](typescript-code-style.instructions.md).

## ESLint Setup

- Using ESLint v9+ with flat configuration format
- Configuration files:
  - `eslint.config.js`: Main flat config file for the project
  - `eslint.config.mjs`: Alternative format for module support

## TypeScript Configuration

- Project references are used to separate concerns:
  - `tsconfig.json`: Root configuration with references
  - `tsconfig.app.json`: App-specific configuration
  - `tsconfig.node.json`: Node-specific configuration
  - `tsconfig.test.json`: Test-specific configuration

## Common ESLint Rules

```javascript
rules: {
  // General formatting rules
  "quotes": ["error", "double"],
  "semi": ["error", "always"],
  "comma-dangle": ["error", "never"],
  "no-trailing-spaces": "error",
  "eol-last": ["error", "always"]
}
```

## Monorepo Path Handling & Ignore Patterns

- **Root ESLint Config**: The repo root contains `eslint.config.js` which imports the frontend config (`web_ui/eslint.config.js`). Always run ESLint and pre-commit from the repo root for correct path resolution.
- **Absolute Ignore Patterns**: Legacy and legacy-adjacent files (e.g., `src/core_daemon/web_ui/`) are excluded using absolute ignore patterns in both ESLint config and pre-commit. Example:
  ```js
  ignores: [
    // ...other ignores...
    path.resolve(__dirname, "../src/core_daemon/web_ui/**"),
  ];
  ```
- **Pre-commit Hook**: The `.pre-commit-config.yaml` is set to run ESLint from the root, using the root config and correct args. It uses absolute ignore patterns to ensure legacy files are not checked.

## Best Practices for Flat Config + Pre-commit

- Always use absolute paths for `tsconfig.eslint.json` and `tsconfigRootDir` in ESLint config.
- Exclude all legacy/legacy-adjacent files in both ESLint and pre-commit configs.
- Run ESLint and pre-commit from the repo root to ensure correct config resolution.
- Use `npm run lint` and `npm run lint:fix` to check/fix only modern code.

## Legacy Code Exclusion

- All files in `src/core_daemon/web_ui/` and other legacy directories are excluded from linting and type checking.
- This is enforced in both ESLint config and pre-commit hook using robust ignore patterns.
- If new legacy files are added, update ignore patterns in both configs.

## ESLint Ignore Patterns for Build/Cache/Output Files

All build, cache, and output files are excluded from linting and type checking. This includes:

- `dist/`, `dist-ssr/`
- `.vite/`, `.vite-temp/`, `node_modules/.vite/`
- `node_modules/`
- `*.tsbuildinfo`
- `.cache/`
- `*.log`

These patterns are enforced in both the monorepo root and `web_ui` ESLint flat configs. If you see lint errors from these files, check your ignore patterns.

## TypeScript Project Reference & ESLint Integration

- ESLint is pointed to the correct `tsconfig.eslint.json` using absolute paths for parserOptions.
- TypeScript project references (`tsconfig.json`, `tsconfig.app.json`, etc.) are used for modularity and performance.
- If ESLint cannot resolve TypeScript config, check that all paths are absolute and that you are running from the repo root.

## Known Issues and Fixes

### TypeScript Interface Parsing Errors

ESLint may produce parsing errors for TypeScript files with standalone interfaces. This happens because ESLint treats files without imports/exports as script files rather than modules.

Fix:

- Ensure all TypeScript files with interfaces have at least one import
- Use the `fix:interfaces` script to add React imports to affected files:
  ```bash
  npm run fix:interfaces
  ```

### Trailing Commas in Configuration Files

ESLint is configured to disallow trailing commas. Use the fix script to remove them:

```bash
npm run fix:style
```

## Pre-Commit Hook Configuration

The pre-commit hook is configured to run ESLint with the `--fix` option:

```yaml
- repo: https://github.com/pre-commit/mirrors-eslint
  rev: v8.56.0
  hooks:
    - id: eslint
      files: \.(js|ts|tsx)$
      types: [file]
      args: ["--fix", "--config", "web_ui/eslint.config.js"]
      additional_dependencies:
        - eslint@9.25.0
        - eslint-plugin-react-hooks@5.2.0
        - eslint-plugin-react-refresh@0.4.19
        - typescript@5.8.3
        - typescript-eslint@8.30.1
        - "@eslint/js@9.26.0"
        - globals@16.0.0
        - eslint-plugin-jsdoc@50.6.17
      exclude: ^web_ui/(dist|node_modules)/
```

## Troubleshooting

If you encounter persistent ESLint errors even after running fix scripts:

1. Check if the file has proper imports (especially for interface-only files)
2. Ensure the tsconfig.app.json includes the file in its paths
3. Try running the specific fix scripts:

   ```
   npm run fix:interfaces  # For TypeScript interface parsing errors
   npm run fix:style       # For styling issues including trailing commas
   ```

4. For persistent errors, check GitHub issue #30 for known issues

## MCP Tool Usage

- Use `@context7` for codebase-specific config, ignore, and legacy exclusion queries (e.g., `@context7 ESLint ignore patterns`, `@context7 legacy exclusion`).
- Use `@perplexity` for external best practices and troubleshooting (e.g., `@perplexity monorepo ESLint flat config`).

## Example ESLint Config Snippet

```js
// eslint.config.js (root)
import webUiConfig from "./web_ui/eslint.config.js";
export default [webUiConfig];
```

```js
// web_ui/eslint.config.js (ignore pattern example)
import path from "path";
export default [
  // ...other config...
  {
    ignores: [
      path.resolve(__dirname, "../src/core_daemon/web_ui/**"),
      // ...other ignores...
    ],
  },
];
```
