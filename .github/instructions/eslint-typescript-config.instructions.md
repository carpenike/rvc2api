---
applyTo: "**/web_ui/**"
---

# ESLint and TypeScript Configuration

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
