#!/usr/bin/env python3

import tomllib
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import tomli_w

# Set working directory to location of script
SCRIPT_DIR: Path = Path(__file__).resolve().parent.parent
ROOT_PYPROJECT: Path = SCRIPT_DIR / "pyproject.toml"
LIBS_DIR: Path = SCRIPT_DIR / "libs"


def parse_dependencies(toml_path: Path) -> Set[str]:
    with toml_path.open("rb") as f:
        toml: Dict[str, Any] = tomllib.load(f)
    deps: Any = toml.get("project", {}).get("dependencies", [])
    return set(deps if isinstance(deps, list) else [])


def parse_dev_dependencies(toml_path: Path) -> Set[str]:
    with toml_path.open("rb") as f:
        toml: Dict[str, Any] = tomllib.load(f)
    # Tries workspace-style or hatch/poetry optional deps style
    dev_group: Any = toml.get("dependency-groups", {}).get("dev", [])
    if dev_group:
        return set(dev_group if isinstance(dev_group, list) else [])
    dev_opts: Any = (
        toml.get("project", {}).get("optional-dependencies", {}).get("dev", [])
    )
    return set(dev_opts if isinstance(dev_opts, list) else [])


def load_pyproject(toml_path: Path) -> Dict[str, Any]:
    with toml_path.open("rb") as f:
        return tomllib.load(f)


def save_pyproject(toml_path: Path, data: Dict[str, Any]) -> None:
    with toml_path.open("wb") as f:
        f.write(tomli_w.dumps(data).encode("utf-8"))


libs_files: List[Path] = list(LIBS_DIR.glob("*/pyproject.toml"))
root_data: Dict[str, Any] = load_pyproject(ROOT_PYPROJECT)
root_deps: Set[str] = set(root_data.get("project", {}).get("dependencies", []))
root_dev_deps: Set[str] = set(root_data.get("dependency-groups", {}).get("dev", []))

merged: Set[str] = set(root_deps)
merged_dev: Set[str] = set(root_dev_deps)
sources: List[Tuple[Path, Set[str]]] = []

for pyproject in libs_files:
    sub_deps: Set[str] = parse_dependencies(pyproject)
    sub_dev_deps: Set[str] = parse_dev_dependencies(pyproject)
    new_deps: Set[str] = sub_deps - merged
    new_dev_deps: Set[str] = sub_dev_deps - merged_dev
    if new_deps:
        print(f"Adding dependencies from {pyproject}: {new_deps}")
        merged |= new_deps
    if new_dev_deps:
        print(f"Adding dev dependencies from {pyproject}: {new_dev_deps}")
        merged_dev |= new_dev_deps
    sources.append((pyproject, new_deps | new_dev_deps))

print("\n--- Merged Dependency List ---")
for dep in sorted(merged):
    print(dep)

print("\n--- Merged Dev Dependency List ---")
for dev_dep in sorted(merged_dev):
    print(dev_dep)

# Update project dependencies and dev dependencies in root pyproject.toml
root_data.setdefault("project", {})
root_data["project"]["dependencies"] = sorted(merged)
root_data.setdefault("dependency-groups", {})
root_data["dependency-groups"]["dev"] = sorted(merged_dev)

# Write updated config back to root pyproject.toml
save_pyproject(ROOT_PYPROJECT, root_data)
print(f"\nUpdated {ROOT_PYPROJECT} dependencies and dev dependencies written.")
