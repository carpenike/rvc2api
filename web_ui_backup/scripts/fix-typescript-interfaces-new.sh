#!/bin/bash
# Fix TypeScript parsing issues with interfaces

echo "Ensuring TypeScript imports are properly handled..."

# Make sure imports are properly formatted for TypeScript files with interfaces
for file in $(find ./src -name "*.ts" -o -name "*.tsx"); do
  # Skip compiled JS files
  if [[ $file == *".js" ]]; then
    continue
  fi

  # Fix interface definitions causing parsing errors by ensuring proper imports
  if grep -q "interface " "$file"; then
    # Check if the file is using imports already
    if ! grep -q "import " "$file"; then
      echo "Adding import to $file"
      # Create a temporary file with the import added at the top
      TMP_FILE=$(mktemp)
      echo '// Ensure file is treated as a module' > "$TMP_FILE"
      echo 'import type { FC } from "react";' >> "$TMP_FILE"
      echo '' >> "$TMP_FILE"
      cat "$file" >> "$TMP_FILE"
      # Replace original file with temporary file
      mv "$TMP_FILE" "$file"
    fi
  fi

  # Fix trailing commas in objects and arrays
  if grep -q ",$" "$file"; then
    echo "Fixing trailing commas in $file"
    TMP_FILE=$(mktemp)
    sed 's/,[ \t]*$//' "$file" > "$TMP_FILE"
    mv "$TMP_FILE" "$file"
  fi
done

# Also check JS config files
for file in $(find . -maxdepth 2 -name "*.js" -o -name "*.config.js" -o -name "*.config.ts"); do
  # Fix trailing commas in objects and arrays
  if grep -q ",$" "$file"; then
    echo "Fixing trailing commas in $file"
    TMP_FILE=$(mktemp)
    sed 's/,[ \t]*$//' "$file" > "$TMP_FILE"
    mv "$TMP_FILE" "$file"
  fi
done

echo "TypeScript interface fixes applied!"
