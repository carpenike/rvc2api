# Deploy Documentation

Complete documentation build and deployment workflow including OpenAPI schema export, MkDocs site generation, and PDF processing for comprehensive API and technical documentation.

## OpenAPI Schema Export

### 1. Generate OpenAPI Documentation
```bash
# Export OpenAPI schema in multiple formats
poetry run python scripts/export_openapi.py

# Verify OpenAPI files were created
echo "=== OpenAPI Schema Files ==="
if [ -f "docs/api/openapi.json" ]; then
    echo "✓ OpenAPI JSON schema exported"
    ls -lh docs/api/openapi.json
else
    echo "✗ OpenAPI JSON schema missing"
fi

if [ -f "docs/api/openapi.yaml" ]; then
    echo "✓ OpenAPI YAML schema exported"
    ls -lh docs/api/openapi.yaml
else
    echo "✗ OpenAPI YAML schema missing"
fi

# Validate OpenAPI schema structure
poetry run python -c "
import json
try:
    with open('docs/api/openapi.json', 'r') as f:
        schema = json.load(f)

    print(f'✓ OpenAPI version: {schema.get(\"openapi\", \"unknown\")}')
    print(f'✓ API title: {schema.get(\"info\", {}).get(\"title\", \"unknown\")}')
    print(f'✓ API version: {schema.get(\"info\", {}).get(\"version\", \"unknown\")}')

    paths = schema.get('paths', {})
    print(f'✓ Total endpoints: {len(paths)}')

    # Show endpoint summary
    for path, methods in list(paths.items())[:5]:
        method_list = ', '.join(methods.keys())
        print(f'  {path}: {method_list}')

    if len(paths) > 5:
        print(f'  ... and {len(paths) - 5} more endpoints')

except Exception as e:
    print(f'✗ Failed to validate OpenAPI schema: {e}')
"
```

### 2. Validate API Documentation Coverage
```bash
# Check that all API endpoints are documented
poetry run python -c "
import asyncio
from backend.main import create_app
from fastapi.openapi.utils import get_openapi

async def validate_api_coverage():
    app = create_app()

    # Get OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    paths = openapi_schema.get('paths', {})

    print('=== API Documentation Coverage ===')

    undocumented_endpoints = []
    documented_count = 0

    for path, methods in paths.items():
        for method, spec in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                if not spec.get('description') or not spec.get('summary'):
                    undocumented_endpoints.append(f'{method.upper()} {path}')
                else:
                    documented_count += 1

    total_endpoints = documented_count + len(undocumented_endpoints)
    coverage_percent = (documented_count / total_endpoints * 100) if total_endpoints > 0 else 0

    print(f'✓ Documented endpoints: {documented_count}')
    print(f'✓ Coverage: {coverage_percent:.1f}%')

    if undocumented_endpoints:
        print(f'⚠ Undocumented endpoints ({len(undocumented_endpoints)}):')
        for endpoint in undocumented_endpoints[:10]:  # Show first 10
            print(f'  - {endpoint}')
        if len(undocumented_endpoints) > 10:
            print(f'  ... and {len(undocumented_endpoints) - 10} more')
    else:
        print('✓ All endpoints are documented')

asyncio.run(validate_api_coverage())
"
```

## MkDocs Documentation Build

### 3. Build MkDocs Site
```bash
# Install MkDocs dependencies if needed
poetry run pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin

# Build documentation site
echo "Building MkDocs documentation..."
poetry run mkdocs build --clean

# Verify build output
if [ -d "site" ]; then
    echo "✓ MkDocs site built successfully"

    # Show build statistics
    site_size=$(du -sh site/ | cut -f1)
    file_count=$(find site/ -type f | wc -l)
    echo "✓ Site size: $site_size"
    echo "✓ Total files: $file_count"

    # Check for critical files
    [ -f "site/index.html" ] && echo "✓ Homepage created" || echo "✗ Homepage missing"
    [ -d "site/api" ] && echo "✓ API docs included" || echo "✗ API docs missing"
    [ -d "site/architecture" ] && echo "✓ Architecture docs included" || echo "✗ Architecture docs missing"

else
    echo "✗ MkDocs build failed"
    exit 1
fi
```

### 4. Validate Documentation Links
```bash
# Check for broken internal links
echo "Validating documentation links..."

poetry run python -c "
import os
import re
from pathlib import Path

def find_broken_links():
    site_dir = Path('site')
    if not site_dir.exists():
        print('✗ Site directory not found')
        return

    broken_links = []
    total_links = 0

    # Find all HTML files
    html_files = list(site_dir.rglob('*.html'))

    for html_file in html_files:
        try:
            content = html_file.read_text(encoding='utf-8')

            # Find internal links (href=\"/...\" or href=\"../...\")
            internal_links = re.findall(r'href=\"([^\"]*\.(?:html|md))\"', content)

            for link in internal_links:
                total_links += 1

                # Resolve relative links
                if link.startswith('/'):
                    target_path = site_dir / link.lstrip('/')
                else:
                    target_path = html_file.parent / link

                # Normalize path
                try:
                    target_path = target_path.resolve()
                    if not target_path.exists():
                        broken_links.append(f'{html_file.relative_to(site_dir)}: {link}')
                except Exception:
                    broken_links.append(f'{html_file.relative_to(site_dir)}: {link} (path error)')

        except Exception as e:
            print(f'Warning: Could not process {html_file}: {e}')

    print(f'✓ Checked {total_links} internal links')

    if broken_links:
        print(f'⚠ Found {len(broken_links)} broken links:')
        for link in broken_links[:10]:  # Show first 10
            print(f'  - {link}')
        if len(broken_links) > 10:
            print(f'  ... and {len(broken_links) - 10} more')
    else:
        print('✓ All internal links are valid')

find_broken_links()
"
```

## Documentation Processing and Enhancement

### 5. Process PDF Documentation
```bash
# Process RV-C specification PDF for documentation integration
if [ -f "resources/rvc-2023-11.pdf" ]; then
    echo "Processing RV-C PDF documentation..."

    # Run document loader to extract and process PDF content
    poetry run python dev_tools/document_loader.py \
        --input resources/rvc-2023-11.pdf \
        --output docs/specs/rvc-extracted.md \
        --format markdown

    # Test document processing
    poetry run python dev_tools/test_document_loader.py

    echo "✓ PDF documentation processed"
else
    echo "ℹ RV-C PDF not found, skipping PDF processing"
fi

# Create documentation chunks for search integration
if [ -f "resources/rvc-2023-11_chunks.json" ]; then
    echo "✓ Document chunks available for search integration"
else
    echo "ℹ Creating document chunks..."
    poetry run python dev_tools/enhanced_document_processor.py \
        --input resources/rvc-2023-11.pdf \
        --output resources/rvc-2023-11_chunks.json \
        --strategy mixed
fi
```

### 6. Generate API Documentation Pages
```bash
# Create detailed API documentation from OpenAPI schema
poetry run python -c "
import json
import yaml
from pathlib import Path

def generate_api_docs():
    # Load OpenAPI schema
    try:
        with open('docs/api/openapi.json', 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print('✗ OpenAPI schema not found. Run OpenAPI export first.')
        return

    # Create API overview documentation
    api_docs_dir = Path('docs/api')
    api_docs_dir.mkdir(exist_ok=True)

    # Generate API overview
    overview_content = f'''# API Overview

{schema.get('info', {}).get('description', 'CoachIQ RV-C API')}

## Version
{schema.get('info', {}).get('version', 'unknown')}

## Base URL
- Development: `http://localhost:8000`
- Production: Configure based on deployment

## Authentication
{schema.get('info', {}).get('x-authentication', 'No authentication required for development')}

## Available Endpoints

'''

    # Add endpoint summary
    paths = schema.get('paths', {})
    for path, methods in sorted(paths.items()):
        overview_content += f'### `{path}`\\n\\n'

        for method, spec in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                summary = spec.get('summary', 'No summary')
                overview_content += f'- **{method.upper()}**: {summary}\\n'

        overview_content += '\\n'

    # Write overview file
    overview_file = api_docs_dir / 'overview.md'
    overview_file.write_text(overview_content)
    print(f'✓ Generated API overview: {overview_file}')

    # Generate OpenAPI markdown documentation
    openapi_md_content = f'''# OpenAPI Specification

## Schema Files

- [JSON Format](openapi.json) - Machine-readable OpenAPI 3.0 schema
- [YAML Format](openapi.yaml) - Human-readable OpenAPI 3.0 schema

## Interactive Documentation

When the server is running, you can access interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Schema Information

- **OpenAPI Version**: {schema.get('openapi', 'unknown')}
- **API Title**: {schema.get('info', {}).get('title', 'unknown')}
- **API Version**: {schema.get('info', {}).get('version', 'unknown')}
- **Total Endpoints**: {len(paths)}

## Endpoints by Tag

'''

    # Group endpoints by tags
    tags = {}
    for path, methods in paths.items():
        for method, spec in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                endpoint_tags = spec.get('tags', ['Untagged'])
                for tag in endpoint_tags:
                    if tag not in tags:
                        tags[tag] = []
                    tags[tag].append(f'{method.upper()} {path}')

    for tag, endpoints in sorted(tags.items()):
        openapi_md_content += f'### {tag}\\n\\n'
        for endpoint in sorted(endpoints):
            openapi_md_content += f'- `{endpoint}`\\n'
        openapi_md_content += '\\n'

    openapi_md_file = api_docs_dir / 'openapi.md'
    openapi_md_file.write_text(openapi_md_content)
    print(f'✓ Generated OpenAPI documentation: {openapi_md_file}')

generate_api_docs()
"
```

## Documentation Deployment

### 7. Prepare for GitHub Pages Deployment
```bash
# Prepare documentation for GitHub Pages deployment
echo "Preparing documentation for deployment..."

# Check if this is a Git repository
if [ -d ".git" ]; then
    echo "✓ Git repository detected"

    # Check current branch
    current_branch=$(git branch --show-current)
    echo "✓ Current branch: $current_branch"

    # Check if gh-pages branch exists
    if git show-ref --verify --quiet refs/heads/gh-pages; then
        echo "✓ gh-pages branch exists"
    else
        echo "ℹ gh-pages branch not found - will be created on first deployment"
    fi

    # Check GitHub Pages configuration
    if [ -f ".github/workflows/docs.yml" ] || [ -f ".github/workflows/pages.yml" ]; then
        echo "✓ GitHub Actions workflow for documentation found"
    else
        echo "ℹ No GitHub Actions workflow found for automated deployment"
    fi

else
    echo "ℹ Not a Git repository - manual deployment required"
fi

# Create deployment-ready documentation
echo "Creating deployment-ready documentation..."

# Ensure all necessary files are present
required_files=(
    "site/index.html"
    "docs/api/openapi.json"
    "mkdocs.yml"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✓ All required files present for deployment"
else
    echo "✗ Missing required files:"
    printf '  - %s\n' "${missing_files[@]}"
    exit 1
fi
```

### 8. Test Documentation Site Locally
```bash
# Serve documentation locally for testing
echo "Starting local documentation server..."

# Start MkDocs development server in background
poetry run mkdocs serve --dev-addr 127.0.0.1:8001 &
MKDOCS_PID=$!

# Wait for server to start
sleep 3

# Test documentation endpoints
echo "Testing documentation endpoints..."

# Test homepage
if curl -f -s http://127.0.0.1:8001/ > /dev/null; then
    echo "✓ Homepage accessible"
else
    echo "✗ Homepage not accessible"
fi

# Test API documentation
if curl -f -s http://127.0.0.1:8001/api/ > /dev/null; then
    echo "✓ API documentation accessible"
else
    echo "✗ API documentation not accessible"
fi

# Test search functionality (if available)
if curl -f -s http://127.0.0.1:8001/search/ > /dev/null; then
    echo "✓ Search functionality accessible"
else
    echo "ℹ Search functionality not available"
fi

# Cleanup
kill $MKDOCS_PID 2>/dev/null || true

echo "✓ Local documentation testing complete"
echo "ℹ Documentation available at: http://127.0.0.1:8001/"
```

## Documentation Quality Assurance

### 9. Validate Documentation Quality
```bash
# Check documentation for common issues
echo "=== Documentation Quality Check ==="

poetry run python -c "
import re
from pathlib import Path

def check_documentation_quality():
    docs_dir = Path('docs')
    if not docs_dir.exists():
        print('✗ Documentation directory not found')
        return

    issues = []
    total_files = 0

    # Check all markdown files
    md_files = list(docs_dir.rglob('*.md'))

    for md_file in md_files:
        total_files += 1

        try:
            content = md_file.read_text(encoding='utf-8')

            # Check for empty files
            if not content.strip():
                issues.append(f'{md_file}: Empty file')
                continue

            # Check for missing titles
            if not re.search(r'^#\s+.+', content, re.MULTILINE):
                issues.append(f'{md_file}: Missing main title')

            # Check for broken image links
            img_links = re.findall(r'!\[.*?\]\(([^)]+)\)', content)
            for img_link in img_links:
                if not img_link.startswith('http') and not (md_file.parent / img_link).exists():
                    issues.append(f'{md_file}: Broken image link: {img_link}')

            # Check for TODO/FIXME comments
            todos = re.findall(r'(?:TODO|FIXME|XXX).*', content, re.IGNORECASE)
            for todo in todos:
                issues.append(f'{md_file}: TODO found: {todo.strip()}')

        except Exception as e:
            issues.append(f'{md_file}: Read error: {e}')

    print(f'✓ Checked {total_files} documentation files')

    if issues:
        print(f'⚠ Found {len(issues)} documentation issues:')
        for issue in issues[:15]:  # Show first 15
            print(f'  - {issue}')
        if len(issues) > 15:
            print(f'  ... and {len(issues) - 15} more issues')
    else:
        print('✓ No documentation quality issues found')

check_documentation_quality()
"
```

### 10. Final Deployment Verification
```bash
echo "=== Final Deployment Verification ==="

# Check build artifacts
echo "Build Artifacts:"
[ -d "site" ] && echo "✓ MkDocs site built" || echo "✗ MkDocs site missing"
[ -f "docs/api/openapi.json" ] && echo "✓ OpenAPI JSON exported" || echo "✗ OpenAPI JSON missing"
[ -f "docs/api/openapi.yaml" ] && echo "✓ OpenAPI YAML exported" || echo "✗ OpenAPI YAML missing"

# Check documentation completeness
echo "Documentation Completeness:"
[ -f "docs/index.md" ] && echo "✓ Main documentation index" || echo "✗ Main index missing"
[ -d "docs/api" ] && echo "✓ API documentation" || echo "✗ API docs missing"
[ -d "docs/architecture" ] && echo "✓ Architecture documentation" || echo "✗ Architecture docs missing"

# Size and performance check
echo "Performance Metrics:"
if [ -d "site" ]; then
    site_size=$(du -sh site/ | cut -f1)
    echo "✓ Site size: $site_size"

    # Check for large files that might slow loading
    large_files=$(find site/ -size +1M -type f 2>/dev/null | wc -l)
    if [ $large_files -gt 0 ]; then
        echo "⚠ Found $large_files files larger than 1MB"
    else
        echo "✓ No oversized files found"
    fi
fi

# Final status
echo "=== Documentation Deployment Ready ==="
echo "✓ Run 'mkdocs gh-deploy' to deploy to GitHub Pages"
echo "✓ Or copy 'site/' directory to your web server"
echo "✓ OpenAPI schema available at docs/api/openapi.json"
```

## Arguments

$ARGUMENTS can specify:
- `--serve` - Start local documentation server after build
- `--deploy` - Automatically deploy to GitHub Pages after build
- `--skip-api` - Skip OpenAPI schema export
- `--skip-pdf` - Skip PDF processing
- `--validate-only` - Only run documentation validation
- `--clean` - Clean all build artifacts before building
- `api-only` - Only generate API documentation
- `site-only` - Only build MkDocs site

## Development Notes

### Documentation Structure
- `docs/` - Source documentation files
- `site/` - Built documentation site (MkDocs output)
- `docs/api/` - API documentation and OpenAPI schemas
- `mkdocs.yml` - MkDocs configuration

### Deployment Options
1. **GitHub Pages**: Use `mkdocs gh-deploy` or GitHub Actions
2. **Manual**: Copy `site/` directory to web server
3. **CI/CD**: Integrate with deployment pipeline

### Troubleshooting
- If OpenAPI export fails, ensure backend dependencies are installed
- For MkDocs build errors, check `mkdocs.yml` configuration
- If links are broken, verify file paths and case sensitivity
- For large site sizes, optimize images and remove unnecessary files

This command provides comprehensive documentation build and deployment workflow for the CoachIQ API and technical documentation.
