# Sync Dependencies

Synchronize and manage dependencies across Poetry, Nix, and frontend package managers with automated conflict detection and resolution.

## Dependency Analysis and Detection

### 1. Analyze Current Dependencies
```bash
# Show current Poetry dependencies
echo "=== Poetry Dependencies ==="
poetry show --tree

# Check for outdated packages
echo "=== Outdated Packages ==="
poetry show --outdated

# Frontend dependencies
echo "=== Frontend Dependencies ==="
cd frontend
npm list --depth=0
npm outdated
cd ..
```

### 2. Detect Unused Dependencies
```bash
# Run automated unused dependency detection
echo "Detecting unused Python dependencies..."
poetry run python scripts/detect_unused_dependencies.py

# Check for unused frontend dependencies
echo "Checking frontend dependencies..."
cd frontend
if command -v npx >/dev/null 2>&1; then
    # Use depcheck if available
    npx depcheck --ignores="@types/*,vite,typescript" || echo "ℹ depcheck not available, install with: npm install -g depcheck"
else
    echo "ℹ npx not available, skipping frontend unused dependency check"
fi
cd ..
```

### 3. Synchronize Dependencies
```bash
# Run comprehensive dependency synchronization
echo "Synchronizing dependencies across environments..."
poetry run python scripts/sync_dependencies.py

# Verify synchronization results
echo "=== Synchronization Results ==="
if [ -f "sync_report.txt" ]; then
    cat sync_report.txt
    rm sync_report.txt
else
    echo "ℹ No sync report generated"
fi
```

## Poetry Environment Management

### 4. Update Poetry Lock File
```bash
# Update Poetry lock file with latest compatible versions
echo "Updating Poetry lock file..."
poetry lock --no-update

# Install updated dependencies
poetry install

# Verify installation integrity
poetry check

# Show dependency resolution
echo "=== Dependency Resolution ==="
poetry show --tree | head -20
echo "(showing first 20 dependencies...)"
```

### 5. Resolve Poetry Conflicts
```bash
# Check for dependency conflicts
echo "Checking for dependency conflicts..."
poetry run python -c "
import pkg_resources
import sys

def check_dependency_conflicts():
    conflicts = []

    try:
        # Get all installed packages
        installed_packages = [pkg for pkg in pkg_resources.working_set]

        for pkg in installed_packages:
            try:
                # Check if package requirements are satisfied
                pkg_resources.require(str(pkg.as_requirement()))
            except pkg_resources.DistributionNotFound as e:
                conflicts.append(f'Missing dependency: {e}')
            except pkg_resources.VersionConflict as e:
                conflicts.append(f'Version conflict: {e}')

    except Exception as e:
        print(f'Error checking conflicts: {e}')
        return

    if conflicts:
        print(f'⚠ Found {len(conflicts)} dependency conflicts:')
        for conflict in conflicts:
            print(f'  - {conflict}')
    else:
        print('✓ No dependency conflicts detected')

check_dependency_conflicts()
"

# Update specific conflicting packages if needed
# poetry update package-name
```

## Nix Environment Synchronization

### 6. Update Nix Flake Dependencies
```bash
# Update Nix flake inputs (if using Nix)
if [ -f "flake.nix" ]; then
    echo "Updating Nix flake dependencies..."

    # Update flake lock file
    nix flake update

    # Test Nix environment after update
    echo "Testing Nix environment..."
    nix develop --command python --version
    nix develop --command poetry --version

    echo "✓ Nix environment updated and tested"
else
    echo "ℹ No flake.nix found, skipping Nix synchronization"
fi
```

### 7. Validate Nix-Poetry Integration
```bash
# Validate Poetry works correctly in Nix environment
if [ -f "flake.nix" ]; then
    echo "Validating Nix-Poetry integration..."

    nix develop --command bash -c "
        echo 'Testing Poetry in Nix environment...'

        # Test Poetry commands
        poetry --version
        poetry env info

        # Test Python environment
        poetry run python -c 'import sys; print(f\"Python: {sys.version}\"); print(f\"Path: {sys.executable}\")'

        # Test key dependencies
        poetry run python -c '
try:
    import fastapi
    import pydantic
    import sqlalchemy
    print(\"✓ Core dependencies available in Nix environment\")
except ImportError as e:
    print(f\"✗ Missing core dependency: {e}\")
'

        echo '✓ Nix-Poetry integration validated'
    "
else
    echo "ℹ Nix not available, skipping Nix-Poetry validation"
fi
```

## Frontend Dependency Management

### 8. Update Frontend Dependencies
```bash
# Update frontend dependencies
echo "Updating frontend dependencies..."
cd frontend

# Check for security vulnerabilities
npm audit

# Fix vulnerabilities if found
if npm audit --audit-level=moderate | grep -q "found"; then
    echo "Fixing npm security vulnerabilities..."
    npm audit fix
fi

# Update package-lock.json
npm update

# Verify frontend still builds after updates
echo "Testing frontend build after dependency updates..."
npm run build

# Test TypeScript compilation
npm run typecheck

# Test linting
npm run lint

cd ..
echo "✓ Frontend dependencies updated and validated"
```

### 9. Cross-Platform Dependency Validation
```bash
# Ensure dependencies work across development platforms
echo "=== Cross-Platform Validation ==="

# Test Python environment
echo "Python Environment:"
poetry run python -c "
import platform
import sys
print(f'Platform: {platform.system()} {platform.release()}')
print(f'Python: {sys.version}')
print(f'Architecture: {platform.machine()}')

# Test critical imports
critical_modules = [
    'fastapi', 'pydantic', 'sqlalchemy', 'alembic',
    'can', 'asyncio', 'json', 'pathlib'
]

failed_imports = []
for module in critical_modules:
    try:
        __import__(module)
    except ImportError:
        failed_imports.append(module)

if failed_imports:
    print(f'✗ Failed imports: {failed_imports}')
else:
    print('✓ All critical modules importable')
"

# Test Node.js environment
echo "Node.js Environment:"
cd frontend
node -e "
console.log('Node.js:', process.version);
console.log('Platform:', process.platform);
console.log('Architecture:', process.arch);

// Test critical packages
const criticalPackages = ['react', 'typescript', 'vite'];
const missing = [];

criticalPackages.forEach(pkg => {
    try {
        require.resolve(pkg);
    } catch (e) {
        missing.push(pkg);
    }
});

if (missing.length > 0) {
    console.log('✗ Missing packages:', missing);
} else {
    console.log('✓ All critical packages available');
}
"
cd ..
```

## Dependency Security and Compliance

### 10. Security Audit and Compliance Check
```bash
# Python security audit
echo "=== Python Security Audit ==="
if command -v safety >/dev/null 2>&1; then
    poetry run safety check
else
    echo "ℹ Installing safety for security audit..."
    poetry add --group dev safety
    poetry run safety check
fi

# Check for known vulnerabilities in specific packages
poetry run python -c "
import pkg_resources
import requests
import json

def check_python_vulnerabilities():
    try:
        # Get installed packages
        installed = [str(pkg.as_requirement()) for pkg in pkg_resources.working_set]

        print(f'Checking {len(installed)} installed packages for known issues...')

        # This is a simplified check - in production, use tools like safety or bandit
        vulnerable_patterns = [
            'pillow<8.3.2',  # Example of known vulnerability pattern
            'urllib3<1.26.5',
            'requests<2.26.0'
        ]

        potential_issues = []
        for pkg_req in installed:
            pkg_name = pkg_req.split('==')[0].lower()
            for pattern in vulnerable_patterns:
                if pattern.split('<')[0].strip() == pkg_name:
                    potential_issues.append(pkg_req)

        if potential_issues:
            print(f'⚠ Potential security issues found:')
            for issue in potential_issues:
                print(f'  - {issue}')
        else:
            print('✓ No obvious security issues detected')

    except Exception as e:
        print(f'Security check error: {e}')

check_python_vulnerabilities()
"

# Frontend security audit
echo "=== Frontend Security Audit ==="
cd frontend
npm audit --audit-level=high
cd ..
```

### 11. Generate Dependency Report
```bash
# Generate comprehensive dependency report
echo "Generating comprehensive dependency report..."

REPORT_FILE="dependency_report_$(date +%Y%m%d_%H%M%S).md"

cat > "$REPORT_FILE" << EOF
# Dependency Report

Generated: $(date)

## Summary

### Backend (Python/Poetry)
\`\`\`
$(poetry show --tree | head -10)
\`\`\`

### Frontend (Node.js/npm)
\`\`\`
$(cd frontend && npm list --depth=0 | head -10)
\`\`\`

## Environment Information

### Python Environment
- Python Version: $(poetry run python --version)
- Poetry Version: $(poetry --version)
- Virtual Environment: $(poetry env info --path)

### Node.js Environment
- Node Version: $(node --version)
- npm Version: $(npm --version)

### System Information
- OS: $(uname -s)
- Architecture: $(uname -m)

## Dependency Analysis

### Outdated Packages
EOF

# Add outdated packages to report
echo "### Python (Poetry)" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
poetry show --outdated >> "$REPORT_FILE" 2>/dev/null || echo "No outdated packages or error checking" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"

echo "### Frontend (npm)" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
cd frontend && npm outdated >> "../$REPORT_FILE" 2>/dev/null || echo "No outdated packages or error checking" >> "../$REPORT_FILE"
cd ..
echo '```' >> "$REPORT_FILE"

# Add security audit results
echo "## Security Audit" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
poetry run safety check >> "$REPORT_FILE" 2>/dev/null || echo "Safety check not available" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"

echo "✓ Dependency report generated: $REPORT_FILE"
```

## Cleanup and Optimization

### 12. Clean and Optimize Dependencies
```bash
echo "=== Dependency Cleanup and Optimization ==="

# Clean Poetry cache
echo "Cleaning Poetry cache..."
poetry cache clear pypi --all --no-interaction

# Remove unused Poetry groups (if any)
# poetry remove --group dev unused-package

# Clean frontend node_modules and reinstall
echo "Cleaning frontend dependencies..."
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..

# Verify everything still works after cleanup
echo "Verifying system functionality after cleanup..."

# Test backend startup
poetry run python -c "
from backend.main import create_app
app = create_app()
print('✓ Backend app creation successful')
"

# Test frontend build
cd frontend
npm run build > /dev/null 2>&1 && echo "✓ Frontend build successful" || echo "✗ Frontend build failed"
cd ..

# Final dependency count
echo "=== Final Dependency Count ==="
python_deps=$(poetry show | wc -l)
frontend_deps=$(cd frontend && npm list --depth=0 2>/dev/null | grep -c "├\|└" || echo "unknown")

echo "✓ Python dependencies: $python_deps"
echo "✓ Frontend dependencies: $frontend_deps"

echo "=== Dependency Synchronization Complete ==="
```

## Arguments

$ARGUMENTS can specify:
- `--update-all` - Update all dependencies to latest compatible versions
- `--security-only` - Only run security audits and fixes
- `--clean` - Clean caches and reinstall dependencies
- `--nix-only` - Only synchronize Nix environment
- `--frontend-only` - Only manage frontend dependencies
- `--backend-only` - Only manage Python/Poetry dependencies
- `--report` - Generate detailed dependency report
- `--dry-run` - Show what would be updated without making changes

## Development Notes

### Dependency Management Tools
- **Poetry**: Python package management with lock files
- **npm**: Frontend package management
- **Nix**: Reproducible development environment (optional)
- **Safety**: Python security vulnerability scanning

### Best Practices
- Always test after dependency updates
- Use lock files to ensure reproducible builds
- Regular security audits for vulnerabilities
- Monitor for unused dependencies to reduce bloat

### Troubleshooting
- If Poetry conflicts occur, try `poetry lock --no-update` then `poetry install`
- For npm issues, delete `node_modules` and `package-lock.json`, then `npm install`
- If Nix environment issues occur, try `nix flake update` and rebuild
- For cross-platform issues, ensure all developers use same Python/Node versions

This command provides comprehensive dependency management across all package managers and environments used in the CoachIQ project.
