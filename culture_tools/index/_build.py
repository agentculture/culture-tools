"""Build orchestration: gate → introspect → assemble → emit static files.

Walks the candidate manifest, certifies each tool, and writes two artifacts under
``out_dir``:

* ``catalog.json`` — the catalog the Astro site renders from;
* ``simple/`` — the static PEP 503 tree (root index + a page per conformant tool).

Conformance is the gate: only healthy tools get a catalog entry and a ``simple/``
page; the rest are recorded under ``catalog.json``'s ``excluded`` for transparency.
Returns a small summary dict (counts + written paths) for the CLI to report.
"""

from __future__ import annotations

import json
from pathlib import Path

from culture_tools import __version__
from culture_tools.index._catalog import build_catalog, build_entry, excluded_record
from culture_tools.index._conformance import Runner, gate
from culture_tools.index._introspect import introspect
from culture_tools.index._manifest import Tool, candidates, default_repos_dir
from culture_tools.index._simple import normalize, pypi_links, render_project, render_root

_SIMPLE_NOTE = (
    "Distribution files are served by PyPI; tools.culture.dev certifies the AgentFront contract."
)


def build(
    out_dir: Path,
    *,
    tools: tuple[Tool, ...] | None = None,
    repos_dir: Path | None = None,
    runner: Runner | None = None,
) -> dict[str, object]:
    """Generate ``catalog.json`` + the static ``simple/`` tree under ``out_dir``."""
    manifest = tools if tools is not None else candidates()
    base = repos_dir if repos_dir is not None else default_repos_dir()

    entries: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    listed_tools: list[Tool] = []

    for tool in manifest:
        verdict = gate(str(tool.repo_path(base)), tool=tool.name, runner=runner)
        if verdict.healthy:
            meta = introspect(tool.name, tool.command, tool.repo_path(base), runner=runner)
            entries.append(build_entry(tool, meta))
            listed_tools.append(tool)
        else:
            excluded.append(excluded_record(verdict))

    catalog = build_catalog(generator_version=__version__, entries=entries, excluded=excluded)

    out_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = out_dir / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    simple_dir = out_dir / "simple"
    simple_dir.mkdir(parents=True, exist_ok=True)
    (simple_dir / "index.html").write_text(
        render_root([t.name for t in listed_tools]), encoding="utf-8"
    )
    for tool in listed_tools:
        project_dir = simple_dir / normalize(tool.name)
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "index.html").write_text(
            render_project(tool.name, pypi_links(tool.pypi), note=_SIMPLE_NOTE),
            encoding="utf-8",
        )

    return {
        "out": str(out_dir),
        "catalog": str(catalog_path),
        "simple": str(simple_dir),
        "listed": len(entries),
        "excluded": len(excluded),
        "candidates": len(manifest),
    }
