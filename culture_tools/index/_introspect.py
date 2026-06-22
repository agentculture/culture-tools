"""Per-tool metadata, gathered from the tool's *own* AgentFront self-description.

The catalog is built from what each tool says about itself — not a hand-written
blurb file. Sources, most-to-least structured:

* ``pyproject.toml`` — version, summary, homepage, dist name (stdlib ``tomllib``);
* ``culture.yaml`` — nick / backend / model (shared parser from ``whoami``);
* ``<command> learn --json`` — purpose + command map (best-effort enrichment;
  tolerant of a missing binary or a differing ``learn`` shape).

All sources degrade gracefully: a missing file or unparseable output yields empty
fields rather than an error, so one ragged tool never breaks a build.
"""

from __future__ import annotations

import json
import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from culture_tools.cli._commands.whoami import parse_agent_fields
from culture_tools.index._conformance import CommandResult, Runner, _default_runner


@dataclass
class ToolMeta:
    """Self-described metadata for one tool."""

    version: str = ""
    summary: str = ""
    homepage: str = ""
    purpose: str = ""
    backend: str = ""
    model: str = ""
    commands: list[dict[str, object]] = field(default_factory=list)


def _read_pyproject(repo: Path) -> dict[str, object]:
    path = repo / "pyproject.toml"
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    project = data.get("project", {})
    return project if isinstance(project, dict) else {}


def _homepage(project: dict[str, object]) -> str:
    urls = project.get("urls", {})
    if isinstance(urls, dict):
        for key in ("Homepage", "homepage", "Repository", "Source"):
            val = urls.get(key)
            if isinstance(val, str) and val:
                return val
    return ""


def _read_identity(repo: Path, *, fallback_nick: str) -> dict[str, str]:
    try:
        text = (repo / "culture.yaml").read_text(encoding="utf-8")
    except OSError:
        return {"nick": fallback_nick, "backend": "unknown", "model": "unknown"}
    return parse_agent_fields(text, fallback_nick=fallback_nick)


def _run_learn(command: str, runner: Runner) -> dict[str, object]:
    """Best-effort ``<command> learn --json``; empty dict on any failure."""
    if runner is _default_runner and shutil.which(command) is None:
        return {}
    try:
        result = runner([command, "learn", "--json"])
    except OSError:
        return {}
    if not isinstance(result, CommandResult) or result.returncode != 0:
        return {}
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def introspect(
    name: str,
    command: str,
    repo: Path,
    *,
    runner: Runner | None = None,
) -> ToolMeta:
    """Gather :class:`ToolMeta` for one tool from its repo + installed command."""
    run = runner or _default_runner
    project = _read_pyproject(repo)
    identity = _read_identity(repo, fallback_nick=name)
    learn = _run_learn(command, run)

    raw_commands = learn.get("commands", [])
    commands = (
        [c for c in raw_commands if isinstance(c, dict)] if isinstance(raw_commands, list) else []
    )

    return ToolMeta(
        version=str(project.get("version", "")),
        summary=str(project.get("description", "")),
        homepage=_homepage(project),
        purpose=str(learn.get("purpose", "")),
        backend=identity.get("backend", "unknown"),
        model=identity.get("model", "unknown"),
        commands=commands,
    )
