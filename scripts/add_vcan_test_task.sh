#!/usr/bin/env bash
# add_vcan_test_task.sh - Add the vCAN test task to VS Code tasks.json

set -e  # Exit on error

TASKS_FILE=".vscode/tasks.json"
TEMP_FILE=$(mktemp)

if [ ! -f "$TASKS_FILE" ]; then
    echo "❌ $TASKS_FILE not found. Make sure you're in the project root directory."
    exit 1
fi

# Define the new task
NEW_TASK=$(cat <<'EOF'
    {
      "label": "System: Test vCAN Setup",
      "type": "shell",
      "command": "cd ${workspaceFolder} && poetry run python dev_tools/test_vcan_setup.py",
      "group": "none",
      "detail": "Test vCAN setup by sending and receiving a message",
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "clear": true,
        "focus": false
      }
    }
EOF
)

# Find the position to insert the new task (before the last task's closing bracket and the array closing bracket)
# This is a simple approach that may need adjustment for different tasks.json structures
awk -v new_task="$NEW_TASK" '
    # Look for the second-to-last closing brace (assuming it marks the end of the last task)
    /^    }$/ {
        last_task_end_line = NR
    }
    # Print everything
    { print }
    # After the second-to-last closing brace, add the new task
    NR == last_task_end_line {
        print ","
        print new_task
    }
' "$TASKS_FILE" > "$TEMP_FILE"

# Check if the file was modified
if diff -q "$TASKS_FILE" "$TEMP_FILE" > /dev/null; then
    echo "❌ Failed to add task. The task may already exist or the file structure is unexpected."
    rm "$TEMP_FILE"
    exit 1
fi

# Backup original file
cp "$TASKS_FILE" "$TASKS_FILE.bak"

# Replace with modified file
mv "$TEMP_FILE" "$TASKS_FILE"

echo "✅ Successfully added 'System: Test vCAN Setup' task to $TASKS_FILE"
echo "   Original file backed up to $TASKS_FILE.bak"
