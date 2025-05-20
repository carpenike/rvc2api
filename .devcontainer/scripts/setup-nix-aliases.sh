#!/bin/bash
# setup-nix-aliases.sh - Set up aliases for improved Nix experience

# Fish shell configuration
if command -v fish &>/dev/null; then
  mkdir -p ~/.config/fish/functions
  echo 'function nix_develop
    /workspace/.devcontainer/scripts/nix-develop-wrapper.sh $argv
end' > ~/.config/fish/functions/nix_develop.fish

  # Create fish alias
  echo "alias nix-develop='/workspace/.devcontainer/scripts/nix-develop-wrapper.sh'" >> ~/.config/fish/config.fish
fi

# Bash configuration
if [ -f ~/.bashrc ]; then
  # Only add if not already there
  if ! grep -q "nix-develop-wrapper" ~/.bashrc; then
    echo "alias nix-develop='/workspace/.devcontainer/scripts/nix-develop-wrapper.sh'" >> ~/.bashrc
  fi
fi

# Zsh configuration
if [ -f ~/.zshrc ]; then
  # Only add if not already there
  if ! grep -q "nix-develop-wrapper" ~/.zshrc; then
    echo "alias nix-develop='/workspace/.devcontainer/scripts/nix-develop-wrapper.sh'" >> ~/.zshrc
  fi
fi

echo "✅ Nix aliases set up successfully"
