# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 (2025-05-21)


### Features

* add .DS_STORE to .gitignore to prevent macOS system files from being tracked ([096c6c9](https://github.com/carpenike/rvc2api/commit/096c6c95d2ae0f15a2ec99abb8677d421fb8ccf7))
* add additional VS Code extensions for enhanced development experience ([ce203f4](https://github.com/carpenike/rvc2api/commit/ce203f4842c137da8454ce69e9a37a4786eb7549))
* add Colima and DevContainer optimization guides, enhance performance configurations, and streamline setup scripts ([224ad21](https://github.com/carpenike/rvc2api/commit/224ad211fe0536ea1def4585717c2d57848d6841))
* add custom fish prompt for improved user experience in devShell ([28c183c](https://github.com/carpenike/rvc2api/commit/28c183cb2799ebfa7fd98cf0f7502df83266cb32))
* add custom shell prompt in devShell for improved user experience ([94f53a6](https://github.com/carpenike/rvc2api/commit/94f53a66748784c073774e0a49f13b533a5e9b34))
* add devcontainer setup for vCAN with updated configurations and scripts ([85b1aa7](https://github.com/carpenike/rvc2api/commit/85b1aa74a05e352581da46d0926adc0fe084c824))
* add devcontainer setup with vCAN support and testing scripts ([fd797dc](https://github.com/carpenike/rvc2api/commit/fd797dc096a2e025b60f1923f5dbc7a64fb1e8ab))
* add documentation for Mermaid diagrams and versioning setup ([3cad495](https://github.com/carpenike/rvc2api/commit/3cad4958f0885b400a554cbdff2aa68a1a0cf482))
* Add entry point script for rvc2api server with module resolution ([5fb882f](https://github.com/carpenike/rvc2api/commit/5fb882ffe60f62edf23392ab9057a56682554dec))
* add environment variable sample file and update devcontainer configuration for improved setup ([25d695a](https://github.com/carpenike/rvc2api/commit/25d695a1bf2f37ad3993e6729b5bfe1fccfcc5ae))
* add ESLint extension for improved JavaScript linting in development environment ([3cf860a](https://github.com/carpenike/rvc2api/commit/3cf860a5da3590a2ce985d6968b4144207da3c42))
* add example environment configuration file for RVC2API ([e8adc4e](https://github.com/carpenike/rvc2api/commit/e8adc4e7267f2d6435257c6ef8f21c7f59ec5307))
* Add frontend build scripts for React application management ([3546b06](https://github.com/carpenike/rvc2api/commit/3546b06e30934710160c2736eea5f1d1a6e4634b))
* add initial Nix flake definition for rvc2api with poetry2nix integration -- doesn't work atm. ([94a733f](https://github.com/carpenike/rvc2api/commit/94a733f6d3ff245cf0436bb77171b1d71572891a))
* add instruction for running Python scripts with Poetry ([495f800](https://github.com/carpenike/rvc2api/commit/495f8009869d9fb116b5fe7115857e892380cde8))
* add linux-modules-extra package installation for enhanced kernel module support ([3703b68](https://github.com/carpenike/rvc2api/commit/3703b68000a69e07fc9b8cb6760a4e5146e6a98c))
* add MAGIC_API_KEY to container environment and update mount path for rvc2api-nix-store ([752f343](https://github.com/carpenike/rvc2api/commit/752f3433a25bcd90a9650a0bdbe9d1bcf7b72989))
* add MAGIC_API_KEY to environment variables and integrate vCAN setup test task ([211d4a0](https://github.com/carpenike/rvc2api/commit/211d4a08575fed3a574056b48768167fb164b3e8))
* Add migration summary document for Web UI transition to React ([e8ccc93](https://github.com/carpenike/rvc2api/commit/e8ccc9339741914a1295b207f1d916e808361618))
* add new PDF resource for RVC 2023 ([c99432d](https://github.com/carpenike/rvc2api/commit/c99432df24e459562050b8e78f81f008cb19ba0a))
* Add Nix and vCAN setup scripts for improved development environment ([59e148f](https://github.com/carpenike/rvc2api/commit/59e148f530e960978732a85a2661b15bbf85c55c))
* add package rule to pin all dependencies in Renovate configuration ([8569ec2](https://github.com/carpenike/rvc2api/commit/8569ec2e51dfdd2f724c54d5e3f108616ef69e16))
* add PDF processing instructions and embedding generation to README ([079f2ca](https://github.com/carpenike/rvc2api/commit/079f2ca2c45951aaf7312d904a4b9cd9a71697b7))
* add SideNav component for improved navigation and integrate lucide-react icons ([56c6952](https://github.com/carpenike/rvc2api/commit/56c6952dff3e9502f22919dff1b332d890139de4))
* add standard C library to development and runtime dependencies ([29b2c38](https://github.com/carpenike/rvc2api/commit/29b2c3874337c36ffc16096e48fdd03f46045309))
* add test scripts for CAN interface auto-detection and vCAN setup ([091c5b2](https://github.com/carpenike/rvc2api/commit/091c5b251c41053dcba9438bdaeeb929d97b5e6c))
* Add Type Check task for Pyright in VSCode configuration ([9075321](https://github.com/carpenike/rvc2api/commit/9075321f95f9c28179137ad66ed966a6c564fc1a))
* Add type stubs for FastAPI and httpx to improve type checking and IDE support ([fac17d0](https://github.com/carpenike/rvc2api/commit/fac17d0ee746a5d4d9c37fca73ad43c1302b33e7))
* Add type stubs for Python CAN library and pyroute2 library ([efaaca0](https://github.com/carpenike/rvc2api/commit/efaaca0b427bc8419a1efe0a927e2fa9d159ab09))
* Add VS Code configuration files for improved development setup ([7084ac4](https://github.com/carpenike/rvc2api/commit/7084ac483ae58ebbc38a0e2c110cf0819cc0dee8))
* clean up .envrc by removing manual override comments for clarity ([3040819](https://github.com/carpenike/rvc2api/commit/3040819297e2c7f55bb190008a9754a203cbdf7a))
* enable flake usage in .envrc for improved environment management ([9ce2b51](https://github.com/carpenike/rvc2api/commit/9ce2b5198f43bd045701d13bc27edcf0f2c4b607))
* Enhance development environment and documentation for rvc2api ([9b74a65](https://github.com/carpenike/rvc2api/commit/9b74a6519b784ef75afead294ada6a7da7b3137b))
* enhance devShell with poetry helper and update usage instructions ([f1e375c](https://github.com/carpenike/rvc2api/commit/f1e375cb0981f9faaaf46ad27edb02ff3d879c84))
* enhance Dockerfile and setup scripts for improved Nix development environment ([e4dd841](https://github.com/carpenike/rvc2api/commit/e4dd841fa62b14b92dc5b279dd29e72e35c741f2))
* enhance ESLint configuration for improved file exclusion and path resolution ([7385464](https://github.com/carpenike/rvc2api/commit/738546459445bc05cde1a3fbb754f62a2ea789f0))
* enhance fish prompt setup to include custom prompt script for improved user experience ([432fec4](https://github.com/carpenike/rvc2api/commit/432fec4505026bd3429fee93ba9000d3bb103934))
* enhance Renovate configuration with new automerge rules and reviewer assignments ([4d8c9d1](https://github.com/carpenike/rvc2api/commit/4d8c9d10e966044aa1da154bc9f47d9e586038d5))
* enhance shell prompt setup for better compatibility in bash and zsh ([45f725c](https://github.com/carpenike/rvc2api/commit/45f725c33bf66e92e994ebf074f7ddb57bf641b4))
* implement CAN interface auto-detection and update CAN bus config retrieval ([82da9ed](https://github.com/carpenike/rvc2api/commit/82da9ed014d3a8d7f1492fcc9923ca6cf4c94b6b))
* implement Nix-based development environment setup with vCAN interface support ([3f44217](https://github.com/carpenike/rvc2api/commit/3f44217a0139a654c94a3df27df0d6a2e22611be))
* initialize web UI with React, Vite, and TypeScript ([3c8eb02](https://github.com/carpenike/rvc2api/commit/3c8eb02cb0aceae14fa923a5728adbf00f8181d5))
* Introduce vector search service for RV-C documentation ([e7f352a](https://github.com/carpenike/rvc2api/commit/e7f352a2f8271f285304e8e389ba06547b53d06e))
* remove faiss-cpu dependency from pyproject.toml ([d4236a8](https://github.com/carpenike/rvc2api/commit/d4236a8d601eb7f4138931d47f107d2457f77d4b))
* remove obsolete Nix setup scripts to streamline development environment ([6eedd72](https://github.com/carpenike/rvc2api/commit/6eedd728857ed7ad939569c64934e1653f958c2d))
* remove poetry virtualenv creation in Dockerfile ([a35cf19](https://github.com/carpenike/rvc2api/commit/a35cf199191fa03e213df7fa83a2a16c85f83c38))
* remove unnecessary chmod command for activate-nix-env.sh in setup script ([ebf6ffe](https://github.com/carpenike/rvc2api/commit/ebf6ffec60ea9f0c77db0bdb6c1ed1e61f439c72))
* restrict eslint hook to specific directory for improved linting scope ([25a226e](https://github.com/carpenike/rvc2api/commit/25a226eae750ba8fe370f187248ee45b9447ba07))
* Standardize on Pyright for type checking (closes [#17](https://github.com/carpenike/rvc2api/issues/17)) ([4bb3763](https://github.com/carpenike/rvc2api/commit/4bb3763f60a6d8883384d7fdf70f9a5ee75235f7))
* unify version management by removing VERSION file and using pyproject.toml as the single source of truth ([7cf0a3f](https://github.com/carpenike/rvc2api/commit/7cf0a3f2450ddf6f788101b81e33cff017fbb1a8))
* update .gitignore to include .devcontainer directories and .DS_STORE ([64d37f0](https://github.com/carpenike/rvc2api/commit/64d37f07458f08b3e1fffa768aaf6f7ea41c33a3))
* update devShell prompt for improved visibility in development environment ([2c2dabd](https://github.com/carpenike/rvc2api/commit/2c2dabd9848359e2c0ee5d951cf82ac23e93c171))
* update Dockerfile and remove obsolete scripts for streamlined Nix development environment ([7f5c0ea](https://github.com/carpenike/rvc2api/commit/7f5c0ea0054e926d4746b01148d3dfe4565f9932))
* Update GitHub Actions workflows for frontend CI and Nix-based CI with caching support ([b6cf007](https://github.com/carpenike/rvc2api/commit/b6cf00743eefc2e40d31fe6b44c606572296d8ae))
* update GitHub Copilot instructions for clarity and modularity ([5a17234](https://github.com/carpenike/rvc2api/commit/5a1723489888a276639ecc0f09183e810b3f1798))
* update mcp.json to include local environment variables for API keys ([66a89fb](https://github.com/carpenike/rvc2api/commit/66a89fbc4519f539747a4bad0379f8a3dc496ee8))
* update nixpkgs locked version and hash in flake.lock ([38384ce](https://github.com/carpenike/rvc2api/commit/38384cedb0500ba1ed14a953edc1bcecc79b34f4))
* update pre-commit checks command to use poetry for improved environment consistency ([b3264fa](https://github.com/carpenike/rvc2api/commit/b3264faba55a7ce5dd4036040eee682747882716))
* Update pre-commit configuration with additional hooks for mixed line endings and large file checks ([2095b22](https://github.com/carpenike/rvc2api/commit/2095b2258c068d71880a8e1cd048cb3daae8876c))
* update Renovate configuration to ignore unstable versions ([05dd0db](https://github.com/carpenike/rvc2api/commit/05dd0db3ca85a24fd8515cc1d0e3c071bd7d472a))


### Bug Fixes

* add default language version and disable virtualenv in pre-commit configuration ([99e5542](https://github.com/carpenike/rvc2api/commit/99e5542de5235b0d285aeaae8355b5dc3e5a78bc))
* correct parameter name from 'bustype' to 'interface' in vCAN setup ([19c2a6b](https://github.com/carpenike/rvc2api/commit/19c2a6bfd7d4fa57049598ba44005cc80a17685a))
* exclude large PDF file from pre-commit checks ([daf7cbc](https://github.com/carpenike/rvc2api/commit/daf7cbc526af1e67c024b190a6f902e8e9e97ceb))
* expand ESLint ignore patterns for better coverage in monorepo ([88cb79b](https://github.com/carpenike/rvc2api/commit/88cb79b20e8e8efd7ef9e85628c9b89ce46465ad))
* Remove mypy type checking configuration from pre-commit setup ([5c037da](https://github.com/carpenike/rvc2api/commit/5c037da2c3ea45a13edf186261e66903f43fcbcb))
* remove unnecessary blank lines in test_app_state.py ([7fcb18a](https://github.com/carpenike/rvc2api/commit/7fcb18ac99ee3fe0ca3c258153ced33edf335544))
* Replace mypy with Pyright as the standardized type checker in poetry2nix integration ([9ccd847](https://github.com/carpenike/rvc2api/commit/9ccd847f5101f5c883951ab429beb1e6207d1621))
* simplify poetry lock check command in pre-commit configuration ([58bd9aa](https://github.com/carpenike/rvc2api/commit/58bd9aa8ca66a4d5ba522dd678ef22e5f70550ef))
* Standardize argument formatting and enhance mypy configuration with additional error codes ([90d0056](https://github.com/carpenike/rvc2api/commit/90d0056f0d8acc418de9f99427883441bcf8ade4))
* update API endpoints for light control and improve error handling in Lights component ([9c8b18c](https://github.com/carpenike/rvc2api/commit/9c8b18cf728d6a67c7cabc3d8e2ec3444788d0b2))
* update ESLint configuration path for improved file detection ([ef30ce9](https://github.com/carpenike/rvc2api/commit/ef30ce960a0b39c2d451d15105d15c1b6f795508))
* Update formatting command to use ruff instead of black in flake.nix ([b01de0c](https://github.com/carpenike/rvc2api/commit/b01de0c196d21ee1d5e6042bcd611cdf5ed888fa))
* update nixpkgs locked version and metadata in flake.lock ([4fafb25](https://github.com/carpenike/rvc2api/commit/4fafb25c72fdfa61dd284ab0582e826d08556a68))
* update nixpkgs locked version and metadata in flake.lock ([efa09fe](https://github.com/carpenike/rvc2api/commit/efa09fe66ef46ca561fb8226dd087eafe8236af5))
* update package dependencies and improve type hints in components ([7263c21](https://github.com/carpenike/rvc2api/commit/7263c21053b8695b98619a57a85dcc8d94cec801))

## [Unreleased]

### Added
- Initial release of rvc2api.
- FastAPI backend for API and WebSocket server.
- RV-C message decoding capabilities.
- Entity management for RV-C devices.
- Web UI for monitoring and control.
- Console client for direct interaction.
- Poetry for dependency management.
- Basic API and decoder tests.
