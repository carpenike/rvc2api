FROM nixos/nix:latest

# Install essential packages
RUN nix-channel --update && \
    nix-env -iA nixpkgs.git nixpkgs.poetry nixpkgs.nodejs nixpkgs.python312 \
    nixpkgs.can-utils nixpkgs.iproute2 nixpkgs.curl nixpkgs.gnumake \
    nixpkgs.gcc nixpkgs.openssl nixpkgs.pkg-config nixpkgs.cacert

# Configure git
RUN git config --global core.autocrlf input
RUN git config --global core.eol lf

# Set environment variables
ENV PYTHONPATH=/workspace:$PYTHONPATH
ENV NODE_OPTIONS=--openssl-legacy-provider
ENV NIX_CONFIG="experimental-features = nix-command flakes"

# Add vcan setup script
COPY ./setup-vcan.sh /usr/local/bin/setup-vcan.sh
RUN chmod +x /usr/local/bin/setup-vcan.sh

WORKDIR /workspace

# Set entrypoint to load vcan and then execute CMD
ENTRYPOINT ["/bin/bash", "-c", "/usr/local/bin/setup-vcan.sh && exec \"$@\"", "--"]
CMD ["bash"]
