# ESLint and TypeScript Troubleshooting Guide

## Common Issues & Quick Fixes

### TypeScript Interface Parsing Errors

**Symptom:** ESLint errors like `Parsing error: The keyword 'interface' is reserved` or `Unexpected token interface`

**Fix:**

```bash
# In web_ui directory:
npm run fix:interfaces
```

This adds a React import to standalone interface files, which enables ESLint to parse them correctly as modules rather than scripts.

### Trailing Comma Errors

**Symptom:** ESLint errors about trailing commas in objects/arrays

**Fix:**

```bash
# In web_ui directory:
npm run fix:style
```

This removes trailing commas in various files including configuration files.

### Line Ending Issues

**Symptom:** ESLint warns about CRLF line endings

**Fix:**

```bash
# Check .gitattributes to ensure LF line endings
* text=auto eol=lf
```

### Pre-commit Hook Failures

If the pre-commit hook fails with ESLint errors:

1. Run `npm run fix:interfaces` first
2. Run `npm run fix:style`
3. Run `npm run lint:fix` to apply automatic ESLint fixes
4. Manually fix any remaining issues

## VS Code Tasks

For convenience, several VS Code tasks have been added:

- **Frontend: Lint (ESLint)** - Run ESLint on the web_ui directory
- **Frontend: Fix Lint Issues (ESLint)** - Apply automatic ESLint fixes
- **Frontend: Fix All Style Issues** - Run the style fix script
- **Frontend: Fix TypeScript Interface Issues** - Fix TypeScript interface parsing issues
- **Frontend: Type Check (TypeScript)** - Run TypeScript type checking

## Configuration Files

- **ESLint:** `web_ui/eslint.config.js` and `web_ui/eslint.config.mjs`
- **TypeScript:** `web_ui/tsconfig.json` (root) and referenced configs
- **Fix Scripts:** `web_ui/scripts/fix-eslint-issues.sh` and `web_ui/scripts/fix-typescript-interfaces.sh`

## Reference Documentation

For more detailed information, see:

- [ESLint and TypeScript Configuration](../docs/eslint-typescript-config.md)
- [GitHub Issue #30](https://github.com/carpenike/rvc2api/issues/30) - Tracking remaining ESLint issues
