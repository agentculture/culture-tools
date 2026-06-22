"""tools.culture.dev index — certify and catalog agent-first CLI tools.

The index's membership rule is the AgentFront contract: a tool is listed iff it
passes ``agentfront cli doctor --strict``. This package owns that gate and the
candidate manifest; the catalog/PEP-503 emitters build on top of it (later
milestones). See ``docs/design/tools-culture-dev.md``.
"""

from __future__ import annotations

from pathlib import Path

from culture_tools.index._build import build
from culture_tools.index._conformance import Verdict, gate
from culture_tools.index._manifest import Tool, candidates, default_repos_dir, find

__all__ = [
    "Tool",
    "Verdict",
    "build",
    "check_all",
    "check_one",
    "check_named",
    "candidates",
    "default_repos_dir",
]


def check_one(tool: Tool, *, repos_dir: Path | None = None, runner=None) -> Verdict:
    """Run the conformance gate for a single candidate tool."""
    base = repos_dir if repos_dir is not None else default_repos_dir()
    return gate(str(tool.repo_path(base)), tool=tool.name, runner=runner)


def check_all(*, repos_dir: Path | None = None, runner=None) -> list[Verdict]:
    """Run the conformance gate for every candidate in the manifest."""
    base = repos_dir if repos_dir is not None else default_repos_dir()
    return [check_one(tool, repos_dir=base, runner=runner) for tool in candidates()]


def check_named(name: str, *, repos_dir: Path | None = None, runner=None) -> Verdict | None:
    """Gate a single tool by manifest name; ``None`` if the name is unknown."""
    tool = find(name)
    if tool is None:
        return None
    return check_one(tool, repos_dir=repos_dir, runner=runner)
