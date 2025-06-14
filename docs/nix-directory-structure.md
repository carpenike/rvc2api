# CoachIQ NixOS Directory Structure

This document explains how CoachIQ organizes its files when deployed via NixOS.

## Single Directory Principle

**ALL CoachIQ data lives under `/var/lib/coachiq/`** - no files in `/etc/`, `/usr/share/`, or other system directories.

## Directory Layout

```
/var/lib/coachiq/
├── reference/          # Read-only reference data
│   ├── rvc.json       # RV-C protocol specification
│   ├── coach_mapping.default.yml
│   └── *.yml          # Coach-specific mappings
├── database/          # SQLite databases
│   └── coachiq.db    # Main application database
├── backups/           # Automatic backups
│   └── coachiq-YYYY-MM-DD-HHMMSS.db
├── config/            # User configuration overrides
├── themes/            # Custom UI themes
├── dashboards/        # Custom dashboard definitions
└── logs/              # Application logs
```

## Permission Model

### Read-Only Reference Data
- **Directory**: `/var/lib/coachiq/reference/`
- **Owner**: root:root
- **Permissions**: 0755 (read-only for service)
- **Managed by**: Nix tmpfiles.d
- **Contents**: RV-C specs, coach mappings from package

### User Data Directories
- **Directories**: All others under `/var/lib/coachiq/`
- **Owner**: coachiq:coachiq
- **Permissions**: 0755
- **Managed by**: Application at runtime

## How It Works

### 1. Package Build Time
```nix
postInstall = ''
  # Reference data bundled with package
  mkdir -p $out/${python.sitePackages}/config
  cp -r $src/config/* $out/${python.sitePackages}/config/
'';
```

### 2. System Configuration
```nix
systemd.tmpfiles.rules = [
  # Create directory structure
  "d /var/lib/coachiq 0755 coachiq coachiq -"
  "d /var/lib/coachiq/reference 0755 root root -"

  # Copy reference data from package (C = copy if not exists)
  "C /var/lib/coachiq/reference 0755 root root - ${package}/config"
];
```

### 3. Runtime Behavior
The application searches for configuration in this order:
1. `./config/` (development)
2. Python package resources (bundled)
3. `/var/lib/coachiq/reference/` (production)

## Benefits

1. **Single Location**: Everything under `/var/lib/coachiq/`
2. **Clear Separation**: Read-only reference vs user data
3. **Atomic Updates**: Reference data updated with package
4. **No System Pollution**: No files in `/etc/` or `/usr/share/`
5. **Backup Friendly**: Single directory to backup
6. **Permission Safety**: Reference data can't be modified

## Environment Variables

- `COACHIQ_PERSISTENCE__DATA_DIR`: Change base directory (default: `/var/lib/coachiq`)
- `COACHIQ_RVC__CONFIG_DIR`: Override reference location (rarely needed)

## Development vs Production

### Development
- Uses `./config/` from project root
- No special permissions needed
- Can modify reference files for testing

### Production (NixOS)
- Reference data in `/var/lib/coachiq/reference/` (read-only)
- User data in other subdirectories (writable)
- Managed by systemd and tmpfiles.d

## Migration Note

If upgrading from an older version that used `/etc/coachiq/` or `/usr/share/coachiq/`:
1. Data will be automatically copied to new location
2. Old directories can be safely removed
3. No configuration changes needed
