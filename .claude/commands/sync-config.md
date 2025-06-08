# Sync Configuration Files

Synchronize configuration files after adding new features, dependencies, or settings.

## Command: `/sync-config`

**Purpose**: Ensures all configuration files are updated consistently when adding new features or dependencies.

### What This Command Does:

1. **Analyzes current feature flags** in `backend/services/feature_flags.yaml`
2. **Checks flake.nix settings** for missing NixOS module options
3. **Verifies environment variable mappings** in flake.nix systemd service
4. **Updates .env.example** with missing environment variables
5. **Validates dependency synchronization** between pyproject.toml and flake.nix

### When to Use:

- After adding new features to `feature_flags.yaml`
- After adding new Python dependencies to `pyproject.toml`
- After implementing new protocols or integrations
- When configuration drift is suspected between files
- Before production deployments

### Configuration Files Checked:

- `backend/services/feature_flags.yaml` (source of truth for features)
- `flake.nix` (NixOS module settings and environment variables)
- `.env.example` (environment variable documentation)
- `pyproject.toml` (Python dependencies)

### Example Usage:

```bash
# After adding a new protocol feature
echo "new_protocol:
  enabled: false
  core: false
  depends_on: [can_interface]
  description: 'New protocol integration'
  custom_setting: true" >> backend/services/feature_flags.yaml

# Run sync to update all config files
/sync-config
```

### Expected Output:

- ✅ Updated flake.nix with new NixOS module options
- ✅ Added environment variable mappings to systemd service
- ✅ Updated .env.example with new variables and documentation
- ✅ Verified dependency consistency
- ⚠️ Warnings for any configuration drift detected

### Manual Steps Required:

Some updates may require manual review:
- Complex feature dependencies
- Custom configuration validation
- Documentation updates in `docs/`
- Frontend configuration updates

### Validation Commands:

After running `/sync-config`, verify with:
```bash
# Check Nix build
nix flake check

# Verify feature flag syntax
poetry run python -c "import yaml; yaml.safe_load(open('backend/services/feature_flags.yaml'))"

# Test environment variable parsing
poetry run python -c "from backend.core.config import Settings; print('Config OK')"
```

This command helps maintain configuration consistency and prevents deployment issues caused by missing or inconsistent settings across the project.
