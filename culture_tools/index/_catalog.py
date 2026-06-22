"""Assemble the catalog payload that the site (and agents) consume.

``catalog.json`` is the single source of truth the Astro front-end renders from.
It lists **conformant** tools (the membership rule) and, for transparency, a
separate ``excluded`` roster of candidates that didn't pass — with the bundles
they failed — so the index is honest about what it dropped and why.
"""

from __future__ import annotations

from culture_tools.index._conformance import Verdict
from culture_tools.index._introspect import ToolMeta
from culture_tools.index._manifest import Tool


def build_entry(tool: Tool, meta: ToolMeta) -> dict[str, object]:
    """A single conformant tool's catalog record."""
    return {
        "name": tool.name,
        "pypi": tool.pypi,
        "repo": tool.repo,
        "homepage": meta.homepage or f"https://github.com/{tool.repo}",
        "version": meta.version,
        "summary": meta.summary,
        "purpose": meta.purpose,
        "backend": meta.backend,
        "model": meta.model,
        "commands": meta.commands,
        "install": f"uv tool install {tool.pypi}",
        "conformant": True,
    }


def excluded_record(verdict: Verdict) -> dict[str, object]:
    """A brief, honest record of a candidate that didn't earn a listing."""
    return {
        "name": verdict.tool,
        "ran": verdict.ran,
        "failing_bundles": list(verdict.failing_bundles),
        "error": verdict.error,
    }


def build_catalog(
    *,
    generator_version: str,
    entries: list[dict[str, object]],
    excluded: list[dict[str, object]],
) -> dict[str, object]:
    """The full ``catalog.json`` payload."""
    return {
        "generated_with": f"culture-tools {generator_version}",
        "contract": "agentfront cli doctor --strict",
        "count": len(entries),
        "tools": sorted(entries, key=lambda e: str(e["name"])),
        "excluded": sorted(excluded, key=lambda e: str(e["name"])),
    }
