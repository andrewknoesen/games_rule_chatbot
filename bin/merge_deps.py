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


def load_pyproject(toml_path: Path) -> Dict[str, Any]:
    with toml_path.open("rb") as f:
        return tomllib.load(f)


def save_pyproject(toml_path: Path, data: Dict[str, Any]) -> None:
    with toml_path.open("wb") as f:
        f.write(tomli_w.dumps(data).encode("utf-8"))


# Find all pyproject.toml files under libs/*/
libs_files: List[Path] = list(LIBS_DIR.glob("*/pyproject.toml"))
root_data: Dict[str, Any] = load_pyproject(ROOT_PYPROJECT)
root_deps: Set[str] = set(root_data.get("project", {}).get("dependencies", []))

merged: Set[str] = set(root_deps)
sources: List[Tuple[Path, Set[str]]] = []

for pyproject in libs_files:
    sub_deps: Set[str] = parse_dependencies(pyproject)
    new_deps: Set[str] = sub_deps - merged
    if new_deps:
        print(f"Adding from {pyproject}: {new_deps}")
        merged |= new_deps
    sources.append((pyproject, new_deps))

print("\n--- Merged Dependency List ---")
for dep in sorted(merged):
    print(dep)

# Update project dependencies in root pyproject.toml
root_data.setdefault("project", {})
root_data["project"]["dependencies"] = sorted(merged)

# Write updated config back to root pyproject.toml
save_pyproject(ROOT_PYPROJECT, root_data)
print(f"\nUpdated {ROOT_PYPROJECT} dependencies written.")
