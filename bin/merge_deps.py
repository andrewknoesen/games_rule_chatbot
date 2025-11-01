import glob
import tomllib
from typing import Any, Dict, List, Set, Tuple

ROOT_PYPROJECT: str = "pyproject.toml"
LIBS_GLOB: str = "libs/*/pyproject.toml"


# --- Parse TOML files ---
def parse_dependencies(toml_path: str) -> Set[str]:
    with open(toml_path, "rb") as f:
        toml: Dict[str, Any] = tomllib.load(f)
    deps: Any = toml.get("project", {}).get("dependencies", [])
    return set(deps if isinstance(deps, list) else [])


# --- Collect dependencies ---
libs_files: List[str] = glob.glob(LIBS_GLOB)
root_deps: Set[str] = parse_dependencies(ROOT_PYPROJECT)

merged: Set[str] = set(root_deps)
sources: List[Tuple[str, Set[str]]] = []

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
