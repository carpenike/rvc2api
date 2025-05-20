FROM mcr.microsoft.com/devcontainers/base:debian@sha256:a04e0d63bb8087c8931947bed44364b3addeb40591949bbec9b18eafe80fc220

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

# 5) Single-user Nix + Poetry, direnv & nodejs
USER vscode
ENV HOME=/home/vscode \
    PATH=/home/vscode/.nix-profile/bin:$PATH \
    PYTHONPATH=/workspace

RUN curl -L https://nixos.org/nix/install | sh \
  && . $HOME/.nix-profile/etc/profile.d/nix.sh \
  && nix-env -iA \
       nixpkgs.poetry \
       nixpkgs.direnv \
       nixpkgs.nodejs \
  && poetry config virtualenvs.create false \
  && printf '%s\n' \
       ". $HOME/.nix-profile/etc/profile.d/nix.sh" \
       "eval \"\$(direnv hook bash)\"" \
     >> $HOME/.bashrc

# 6) Fish hook for direnv
RUN mkdir -p $HOME/.config/fish/conf.d \
  && echo 'eval (direnv hook fish)' > $HOME/.config/fish/conf.d/direnv.fish

# 7) Point Git at the system gpg
RUN git config --global gpg.program /usr/bin/gpg

# 8) Cleanup
USER root
RUN apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*

# 9) Back to vscode with bash as default shell
ENV SHELL=/bin/bash
USER vscode
