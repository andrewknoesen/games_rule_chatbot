import os
import sys

pkg_dir: str = sys.argv[1]  # Pass the package directory as an argument


def generate_index(pkg_dir: str) -> None:
    files: list[str] = os.listdir(pkg_dir)
    html = "<html><body>\n"
    for f in sorted(files):
        if f.endswith(".whl") or f.endswith(".tar.gz"):
            html += f'<a href="{f}">{f}</a><br/>\n'
    html += "</body></html>\n"
    with open(os.path.join(pkg_dir, "index.html"), "w") as output:
        output.write(html)


generate_index(pkg_dir)
