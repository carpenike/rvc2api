#!/usr/bin/env python3
"""
check_nixpkgs_versions.py: CI script to ensure Poetry dependencies are available in Nixpkgs.
Usage: python check_nixpkgs_versions.py pyproject.base.toml pyproject.toml
"""

import subprocess
import sys

import toml  # type: ignore
from packaging.specifiers import SpecifierSet
from packaging.version import Version


def get_deps(filename):
    data = toml.load(filename)
    return data["tool"]["poetry"]["dependencies"]


def nixpkgs_version(pkg):
    # Try the poetry name as-is (lowercased, dashes to underscores)
    nix_name = pkg.lower().replace("-", "_")
    name_map = {
        # Add only known mismatches here, e.g. "pillow": "Pillow"
        # "pillow": "Pillow",
    }
    try:
        out = subprocess.check_output(
            [
                "nix",
                "eval",
                "--raw",
                f"with import <nixpkgs> {{}}; python3Packages.{nix_name}.version",
            ],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        nix_name2 = name_map.get(pkg.lower(), nix_name)
        if nix_name2 != nix_name:
            try:
                out = subprocess.check_output(
                    [
                        "nix",
                        "eval",
                        "--raw",
                        f"with import <nixpkgs> {{}}; python3Packages.{nix_name2}.version",
                    ],
                    stderr=subprocess.DEVNULL,
                )
                return out.decode().strip()
            except Exception:
                pass
        print(
            f"::warning::Dependency '{pkg}' not found in nixpkgs as '{nix_name}'. "
            f"Add to name_map if needed."
        )
        return None


def main(base, new):
    base_deps = get_deps(base)
    new_deps = get_deps(new)
    for dep, new_val in new_deps.items():
        if dep == "python":
            continue
        old_val = base_deps.get(dep)
        if old_val == new_val:
            continue  # Not changed
        # Get version specifier
        spec = new_val.get("version", "") if isinstance(new_val, dict) else new_val
        if not spec:
            continue
        nixver = nixpkgs_version(dep)
        if not nixver:
            print(
                f"::error::Dependency '{dep}' not found in nixpkgs. "
                "Please update flake.nix or use a compatible version."
            )
            sys.exit(1)
        # Check if nixpkgs version satisfies the spec
        try:
            if not SpecifierSet(spec).contains(Version(nixver)):
                print(
                    f"::error::Dependency '{dep}' version {spec} not available in nixpkgs "
                    f"(found {nixver})"
                )
                sys.exit(1)
        except Exception as e:
            print(f"::warning::Could not check '{dep}': {e}")
    print("All changed dependencies are available in nixpkgs.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
