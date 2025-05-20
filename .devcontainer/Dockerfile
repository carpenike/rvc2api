FROM mcr.microsoft.com/devcontainers/base:debian

# 1) Install system dependencies (including xz-utils for Nix installer)
RUN set -euxo pipefail \
  && apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       xz-utils \
       coreutils findutils procps util-linux bash curl wget git \
       ca-certificates gnupg lsb-release iproute2 can-utils \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 2) Configure sudo for vscode user
RUN echo "vscode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vscode \
  && chmod 0440 /etc/sudoers.d/vscode

# 3) Switch to vscode user for single-user Nix install
USER vscode
ENV HOME=/home/vscode \
    PATH=/home/vscode/.nix-profile/bin:${PATH}

# 4) Install Nix (single-user), then Poetry + direnv via nix-env
RUN set -euxo pipefail \
  && curl -L https://nixos.org/nix/install | sh \
  && . $HOME/.nix-profile/etc/profile.d/nix.sh \
  && nix-env -iA nixpkgs.poetry nixpkgs.direnv \
  && poetry config virtualenvs.create false \
  && echo '\
. $HOME/.nix-profile/etc/profile.d/nix.sh\n\
eval "$(direnv hook bash)"\
' >> $HOME/.bashrc

# 5) Add direnv hook for fish shell
RUN mkdir -p $HOME/.config/fish/conf.d \
  && echo 'eval (direnv hook fish)' > $HOME/.config/fish/conf.d/direnv.fish

# 6) Python workspace settings
ENV PYTHONPATH=/workspace:${PYTHONPATH}

# 7) Final cleanup (as root) to reclaim space
USER root
RUN apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*

# 8) Set default shell and switch back to vscode
ENV SHELL=/bin/bash
USER vscode
