#!/bin/bash
set -e

fail=0

for release_file in libs/*/RELEASE.md; do
    package_dir=$(dirname "$release_file")
    pyproject="$package_dir/pyproject.toml"
    version=$(awk -F '"' '/^version =/ {print $2}' "$pyproject")

    awk -v ver="$version" -v file="$release_file" '
        $0 ~ "^## "ver"$" {found=1; next}
        found && $0 ~ "^## " {exit}
        found && NF {nonempty=1}
        END {
            if (!found) {
                print file ": Release notes section for version " ver " not found." > "/dev/stderr"
                exit 1
            }
            if (!nonempty) {
                print file ": Release notes for " ver " are empty." > "/dev/stderr"
                exit 1
            }
            print file ": Release notes for " ver " are present and nonempty."
        }
    ' "$release_file" || fail=1
done

exit $fail
