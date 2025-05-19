# GitHub Actions Workflows

This directory contains GitHub Actions workflows for building, testing, and deploying the rvc2api project.

## Workflows

### deploy-docs.yml

This workflow builds and deploys the MkDocs documentation to GitHub Pages whenever changes are made to the docs folder or mkdocs.yml file.

### deploy-deb-repo.yml

This workflow is for building and deploying the Debian package repository. It is currently disabled by default and needs to be configured before use.

### deploy-combined.yml

This workflow combines both documentation and Debian package repository deployment. It builds and deploys the documentation on every push to main, and additionally builds and deploys the Debian repository when a new tag is pushed.

## Configuration

To enable these workflows:

1. Go to your GitHub repository settings
2. Navigate to "Pages"
3. Under "Build and deployment", select "GitHub Actions" as the source
4. Enable the GitHub Pages feature

## Custom Domain (Optional)

If you want to use a custom domain for your GitHub Pages site:

1. Add your custom domain in the repository settings under "Pages"
2. Create a CNAME file in the root of your documentation
3. Add DNS records for your domain
