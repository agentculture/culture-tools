"""The candidate manifest — which tools tools.culture.dev considers for the index.

A *candidate* is a tool we attempt to certify; whether it actually lands in the
index is decided by the conformance gate (:mod:`culture_tools.index._conformance`),
never by appearing here. v1 hand-maintains this list; auto-discovery from the
``agentculture`` GitHub org / PyPI is a later enhancement (see
``docs/design/tools-culture-dev.md``).

Each tool names its installed ``command``, its ``pypi`` distribution, its source
``repo`` (``org/name`` on GitHub), and the ``repo_dir`` basename used to locate a
local checkout. The conformance gate audits ``<repos_dir>/<repo_dir>``;
``repos_dir`` defaults to the parent of this repo (the standard sibling-checkout
layout) and is overridable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from culture_tools.cli._commands.whoami import find_culture_yaml


@dataclass(frozen=True)
class Tool:
    """A candidate tool for the index."""

    name: str
    command: str
    pypi: str
    repo: str
    repo_dir: str

    def repo_path(self, repos_dir: Path) -> Path:
        return repos_dir / self.repo_dir


# Starter manifest. Conservative: tools known to ship an agent-first CLI. The
# gate still decides — a name here that fails `agentfront cli doctor --strict`
# is reported and excluded, not listed.
MANIFEST: tuple[Tool, ...] = (
    Tool("agentfront", "agentfront", "agentfront", "agentculture/agentfront", "agentfront"),
    Tool("devex", "devex", "devex", "agentculture/devex", "devex"),
    Tool("agtag", "agtag", "agtag", "agentculture/agtag", "agtag"),
    Tool("colleague", "colleague", "colleague", "agentculture/colleague", "colleague"),
    Tool("auntiepypi", "auntie", "auntiepypi", "agentculture/auntiepypi", "auntiepypi"),
    Tool(
        "cultureflare", "cultureflare", "cultureflare", "agentculture/cultureflare", "cultureflare"
    ),
    Tool(
        "culture-tools",
        "culture-tools",
        "culture-tools",
        "agentculture/culture-tools",
        "culture-tools",
    ),
)


def default_repos_dir() -> Path:
    """The sibling-checkout root: the parent of this repo.

    Falls back to the current working directory's parent when this package is not
    running from a source checkout (no ``culture.yaml`` found alongside it).
    """
    cfg = find_culture_yaml()
    repo_root = cfg.parent if cfg is not None else Path.cwd()
    return repo_root.parent


def candidates() -> tuple[Tool, ...]:
    return MANIFEST


def find(name: str) -> Tool | None:
    for tool in MANIFEST:
        if tool.name == name:
            return tool
    return None
