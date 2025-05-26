FROM mcr.microsoft.com/devcontainers/base:debian

# 0) Make /bin/sh point at bash so pipefail works everywhere
USER root
RUN ln -sf /bin/bash /bin/sh

# 1) Switch all RUNs to bash with strict flags
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

# 2) Install system dependencies (including coreutils for `sleep`)
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       xz-utils coreutils findutils procps util-linux curl wget git \
       ca-certificates gnupg lsb-release iproute2 can-utils \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 3) Give vscode passwordless sudo
RUN echo "vscode ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/vscode \
  && chmod 0440 /etc/sudoers.d/vscode

# 4) Bake in your nix.conf so the installer picks up your settings
COPY nix.conf /etc/nix/nix.conf

# 5) Install Nix in single-user mode as vscode
USER vscode
ENV HOME=/home/vscode
ENV PATH=/home/vscode/.nix-profile/bin:/home/vscode/.nix-profile/sbin:$PATH

RUN curl -L https://nixos.org/nix/install | sh

# 6) Configure Nix and install required packages
RUN . $HOME/.nix-profile/etc/profile.d/nix.sh \
    && mkdir -p $HOME/.config/nix \
    && echo 'experimental-features = nix-command flakes' > $HOME/.config/nix/nix.conf \
    && nix-channel --add https://nixos.org/channels/nixpkgs-unstable nixpkgs \
    && nix-channel --update \
    && nix-env -iA nixpkgs.poetry nixpkgs.direnv nixpkgs.nodejs

# 7) Fish hook for direnv
RUN mkdir -p $HOME/.config/fish/conf.d \
  && echo 'eval (direnv hook fish)' > $HOME/.config/fish/conf.d/direnv.fish

# 8) Point Git at the system gpg
RUN git config --global gpg.program /usr/bin/gpg

# 9) Cleanup (as root)
USER root
RUN apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*

# 10) Back to vscode with bash as default shell
ENV SHELL=/bin/bash
USER vscode
