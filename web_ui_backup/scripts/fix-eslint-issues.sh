#!/bin/bash
# Fix common ESLint issues in JS/TS files

# Fix TypeScript interface issues first
echo "Fixing TypeScript interface issues..."
./scripts/fix-typescript-interfaces.sh || true

# Apply standard ESLint fixes
echo "Applying ESLint fixes with new config..."
npx eslint --config eslint.config.js . --ext .ts,.tsx --fix || true

echo "Fixing trailing commas in configuration files..."

# Fix specific files
FILES_TO_CHECK=(
  "postcss.config.js"
  "tailwind.config.js"
  "vite.config.ts"
  "jest.config.ts"
  "jest.config.js"
  "src/utils/config.ts"
)

for file in "${FILES_TO_CHECK[@]}"; do
  echo "Checking $file..."
  if [ -f "$file" ]; then
    # Generic fix for trailing commas at end of lines before closing brackets or braces
    TMP_FILE=$(mktemp)
    sed 's/,[ \t]*\([\]}]\)/\1/g' "$file" > "$TMP_FILE"
    mv "$TMP_FILE" "$file"
    echo "Fixed $file"
  fi
done

echo "Fixes applied!"
