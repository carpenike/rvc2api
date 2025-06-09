# VS Code Configuration for CoachIQ

This directory contains VS Code settings optimized for developing the CoachIQ project.

## Setup Requirements

1. **Nix with Flakes**: Ensure Nix is installed with flakes enabled

   ```bash
   # In ~/.config/nix/nix.conf or /etc/nix/nix.conf
   experimental-features = nix-command flakes
   ```

2. **direnv**: Install direnv and configure shell integration

   ```bash
   # For fish shell
   fish_add_path ~/.nix-profile/bin
   direnv hook fish | source
   ```

3. **VS Code Extensions**: Install recommended extensions

   - Press `Cmd+Shift+P` and select "Extensions: Show Recommended Extensions"
   - Install extensions from the recommendations list

   The extensions are categorized into:

   - **Python Development**: Language support, formatting, linting, and FastAPI tools
   - **Nix Development**: Nix language support and environment integration
   - **Frontend Development**: React, TypeScript, Vite, and Tailwind CSS tools
   - **General Tools**: JSON, YAML, and GitHub Copilot for AI assistance

## Configuration Notes

- **Python Interpreter**: The settings use `python` instead of a hardcoded path, relying on direnv to provide the correct environment
- **Code Formatting**: Automatic formatting is configured for Python, TypeScript, JavaScript, JSON, YAML, and HTML files
- **Path Management**: The configuration avoids hardcoded Nix store paths, making it resilient to Nix updates

## Development Workflow

1. Open the project folder in VS Code
2. direnv will automatically load the environment from the flake
3. VS Code will use the Python interpreter and dependencies from this environment
4. For the React frontend, run `cd frontend && npm run dev` for development

## Troubleshooting

- **Python Interpreter Not Found**: If VS Code doesn't detect the Python interpreter, use the command palette (`Cmd+Shift+P`) and select "Python: Select Interpreter", then choose from the list
- **Import Errors**: If imports aren't resolved correctly, restart the VS Code window after direnv has loaded the environment

## Additional Resources

- [Nix Flakes Documentation](https://nixos.wiki/wiki/Flakes)
- [direnv Documentation](https://direnv.net/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [VS Code Python Extension](https://code.visualstudio.com/docs/python/python-tutorial)
