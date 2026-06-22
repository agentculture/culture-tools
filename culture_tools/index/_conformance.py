"""AgentFront conformance gate — the membership rule for tools.culture.dev.

A tool belongs in the index **iff** ``agentfront cli doctor <repo> --strict``
reports healthy. This module delegates to that canonical auditor (``agentfront``,
formerly ``teken`` / ``afi-cli``) and parses its ``--json`` verdict — it does not
reimplement the seven-bundle rubric. Keeping the verdict authoritative is the
whole point: the index certifies the *same* contract the tools are scaffolded
against.

The command runner is injectable (:data:`Runner`) so tests assert on parsing and
gate logic without shelling out.
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404 - we invoke a fixed, trusted binary (agentfront)
from collections.abc import Callable, Sequence
from dataclasses import dataclass

AGENTFRONT_BIN = "agentfront"


@dataclass
class CommandResult:
    """Outcome of running the conformance auditor."""

    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[Sequence[str]], CommandResult]


@dataclass
class Verdict:
    """The conformance verdict for one tool.

    ``healthy`` is the membership signal. ``error`` is set when the gate could
    not run at all (auditor missing, repo absent, unparseable output) — distinct
    from a tool that ran and simply failed the rubric.
    """

    tool: str
    healthy: bool
    failing_bundles: tuple[str, ...] = ()
    error: str = ""

    @property
    def ran(self) -> bool:
        """True when the auditor produced a verdict (vs. failing to run)."""
        return not self.error

    def to_dict(self) -> dict[str, object]:
        return {
            "tool": self.tool,
            "healthy": self.healthy,
            "failing_bundles": list(self.failing_bundles),
            "ran": self.ran,
            "error": self.error,
        }


def _default_runner(cmd: Sequence[str]) -> CommandResult:
    proc = subprocess.run(  # nosec B603 - fixed argv, no shell, trusted binary
        list(cmd),
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def auditor_available(runner: Runner | None = None) -> bool:
    """True when the conformance auditor can be invoked.

    Only meaningful for the real runner — an injected runner is assumed callable.
    """
    if runner is not None and runner is not _default_runner:
        return True
    return shutil.which(AGENTFRONT_BIN) is not None


def parse_verdict(tool: str, result: CommandResult) -> Verdict:
    """Turn an ``agentfront cli doctor --json`` result into a :class:`Verdict`.

    Reads the canonical ``healthy`` field; collects the distinct ``bundle`` names
    of every failed check so a consumer can show *why* a tool is out.
    """
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return Verdict(
            tool,
            healthy=False,
            error=f"could not parse agentfront output (exit {result.returncode})",
        )
    checks = data.get("checks", [])
    failing = tuple(
        sorted({str(c.get("bundle", "?")) for c in checks if not c.get("passed", False)})
    )
    return Verdict(tool, healthy=bool(data.get("healthy")), failing_bundles=failing)


def gate(
    repo: str,
    *,
    tool: str,
    runner: Runner | None = None,
    strict: bool = True,
) -> Verdict:
    """Run the conformance auditor against ``repo`` and return its :class:`Verdict`.

    ``repo`` is a path to the tool's source checkout (``agentfront cli doctor`` is
    a hybrid auditor — it needs the repo, not just the installed binary).
    """
    run = runner or _default_runner
    if not auditor_available(run):
        return Verdict(
            tool,
            healthy=False,
            error=f"{AGENTFRONT_BIN} not on PATH — install it (uv tool install agentfront)",
        )
    cmd = [AGENTFRONT_BIN, "cli", "doctor", str(repo), "--json"]
    if strict:
        cmd.append("--strict")
    return parse_verdict(tool, run(cmd))
