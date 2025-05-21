# Documentation Versioning Updates

This document summarizes the changes made to the documentation versioning system.

## Changes Made

1. **Bash Scripts**: Converted fish-specific scripts to standard bash scripts for broader compatibility:

   - `scripts/docs_version.fish` → `scripts/docs_version.sh`
   - `scripts/setup_versioned_docs.fish` → `scripts/setup_versioned_docs.sh`

2. **Source of Truth**: Changed the source of truth for version information:

   - From: `VERSION` file
   - To: `pyproject.toml` (where release-please already updates the version)

3. **GitHub Actions**: Updated workflows to read version from pyproject.toml when needed:

   - Added pyproject.toml version extraction to `deploy-versioned-docs.yml`
   - Removed `--rebase` flag from mike commands in `deploy-docs.yml`

4. **VS Code Tasks**: Updated VS Code tasks to use the new bash scripts:

   - Added tasks for common documentation versioning operations
   - All tasks now indirectly read version from pyproject.toml
   - Made sure all Python-related tasks use poetry

5. **Error Handling**: Fixed error output and broken pipe issues:

   - Added proper error handling in bash scripts
   - Redirected stderr to suppress broken pipe errors
   - Added `set -e` and `set -o pipefail` for better error handling

6. **Documentation**: Updated documentation to reflect these changes:
   - Updated `docs-versioning-fixes.md`
   - Updated `versioning-with-release-please.md`

## Benefits

1. **Single Source of Truth**: Version information is now stored only in pyproject.toml, eliminating the need to keep multiple files in sync.

2. **Better Integration with release-please**: When release-please updates the version, the documentation versioning system automatically picks it up.

3. **Cross-Platform Compatibility**: Standard bash scripts work in more environments than fish-specific scripts.

4. **Simpler Workflows**: No need to manage a separate VERSION file anymore.

## Testing

The new scripts have been tested and work correctly:

- `./scripts/docs_version.sh list` shows the available documentation versions
- The scripts correctly extract the version from pyproject.toml
- VS Code tasks work properly with the new scripts

## Next Steps

1. **Remove the Old Fish Scripts**: Once everyone has migrated to the new bash scripts, we can remove the old fish scripts.

2. ✅ **VERSION File Removed**: The VERSION file has been removed, and the project now exclusively uses pyproject.toml as the source of truth.

3. **Update Documentation**: Make sure all documentation references the new approach.

4. **Communicate the Change**: Let contributors know about the change to using pyproject.toml as the source of truth for version information.
