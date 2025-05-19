#!/usr/bin/env bash
# Script to generate a GPG key for the Debian repository

# Exit on error
set -e

# Variables
KEY_NAME="rvc2api Repository Key"
KEY_EMAIL="repo@example.com"
KEY_COMMENT="rvc2api Debian Repository Signing Key"
OUTPUT_DIR="debian-repo"

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Generate key batch file
cat > "${OUTPUT_DIR}/gpg-key-gen.batch" << EOF
%echo Generating a basic OpenPGP key for the rvc2api repository
Key-Type: RSA
Key-Length: 4096
Name-Real: ${KEY_NAME}
Name-Comment: ${KEY_COMMENT}
Name-Email: ${KEY_EMAIL}
Expire-Date: 0
%no-ask-passphrase
%no-protection
%commit
%echo Key generation complete
EOF

# Generate the GPG key
echo "Generating GPG key..."
gpg --batch --gen-key "${OUTPUT_DIR}/gpg-key-gen.batch"

# Export the public key
echo "Exporting public key..."
gpg --armor --export "${KEY_EMAIL}" > "${OUTPUT_DIR}/KEY.gpg"

# Clean up
rm "${OUTPUT_DIR}/gpg-key-gen.batch"

echo "GPG key generation complete."
echo "Public key saved to ${OUTPUT_DIR}/KEY.gpg"
echo ""
echo "To use this key in the GitHub workflow, add it as a secret:"
echo "1. Base64 encode the private key:"
echo "   gpg --export-secret-keys --armor ${KEY_EMAIL} | base64 | tr -d '\n'"
echo "2. Add the output as a GitHub secret named GPG_SIGNING_KEY"
