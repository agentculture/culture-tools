"""Markdown catalog for ``culture-tools explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty tuple
and ``("culture-tools",)`` both resolve to the root entry.

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# culture-tools

A clonable template for AgentCulture mesh agents. It carries an agent-first CLI
(cited from the teken `python-cli` reference), a mesh identity (`culture.yaml` +
`CLAUDE.md`), the canonical guildmaster skill kit under `.claude/skills/`, and a
buildable/deployable package baseline. Clone it, rename the package, edit
`culture.yaml`, and you have a new agent.

## Verbs

- `culture-tools whoami` — identity probe from `culture.yaml`.
- `culture-tools learn` — structured self-teaching prompt.
- `culture-tools explain <path>` — markdown docs for any noun/verb.
- `culture-tools overview` — descriptive snapshot of the agent.
- `culture-tools doctor` — check the agent-identity invariants.
- `culture-tools cli overview` — describe the CLI surface.
- `culture-tools index check` — run the AgentFront conformance gate over the tool index.

## Exit-code policy

- `0` success
- `1` user-input error
- `2` environment / setup error
- `3+` reserved

## See also

- `culture-tools explain whoami`
- `culture-tools explain doctor`
"""

_WHOAMI = """\
# culture-tools whoami

Reports the agent's identity from `culture.yaml`: nick (`suffix`), backend,
served model, and the package version. Read-only.

## Usage

    culture-tools whoami
    culture-tools whoami --json
"""

_LEARN = """\
# culture-tools learn

Prints a structured self-teaching prompt covering purpose, command map,
exit-code policy, `--json` support, and the `explain` pointer.

## Usage

    culture-tools learn
    culture-tools learn --json
"""

_EXPLAIN = """\
# culture-tools explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help` (terse,
positional), `explain` is global and addressable by path.

## Usage

    culture-tools explain culture-tools
    culture-tools explain whoami
    culture-tools explain --json <path>
"""

_OVERVIEW = """\
# culture-tools overview

Read-only descriptive snapshot of the agent: identity (from `culture.yaml`), the
verb surface, and the sibling-pattern artifacts the template carries. Accepts an
ignored `target` so a stray path never hard-fails.

## Usage

    culture-tools overview
    culture-tools overview --json
"""

_DOCTOR = """\
# culture-tools doctor

Checks the agent-identity invariants `steward doctor` verifies:
prompt-file-present and backend-consistency (`colleague` → `AGENTS.colleague.md`), plus a
skills-present check. Exits 1 when unhealthy.

## Usage

    culture-tools doctor
    culture-tools doctor --json
"""

_CLI = """\
# culture-tools cli

Noun group for CLI-surface introspection. `cli overview` describes the CLI
itself (distinct from the global `overview`, which describes the agent).

## Usage

    culture-tools cli overview
    culture-tools cli overview --json
"""

_INDEX = """\
# culture-tools index

Certify and catalog agent-first CLI tools for tools.culture.dev. A tool is listed
**iff** it passes the AgentFront contract — the gate delegates to
`agentfront cli doctor <repo> --strict` (the canonical seven-bundle rubric) and
never reimplements it. Non-conformant candidates are reported and excluded.

## Verbs

- `culture-tools index check [TOOL]` — gate every candidate (or one) and report.
- `culture-tools index build [--out DIR]` — emit `catalog.json` + the static PEP
  503 `/simple/` tree for the conformant tools (non-conformant ones are recorded
  under `catalog.json`'s `excluded` roster).
- `culture-tools index overview` — describe this noun's surface.

## Usage

    culture-tools index check
    culture-tools index check agentfront --json
    culture-tools index build --out build/index
    culture-tools index overview
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    ("culture-tools",): _ROOT,
    ("whoami",): _WHOAMI,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
    ("overview",): _OVERVIEW,
    ("doctor",): _DOCTOR,
    ("cli",): _CLI,
    ("cli", "overview"): _CLI,
    ("index",): _INDEX,
    ("index", "check"): _INDEX,
    ("index", "build"): _INDEX,
    ("index", "overview"): _INDEX,
}
