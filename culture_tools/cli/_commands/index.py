"""``culture-tools index`` — certify and catalog agent-first CLI tools.

The index noun is what makes this repo *tools.culture.dev* rather than just a
template: it runs the AgentFront conformance gate over the candidate manifest and
reports which tools earn a place in the index.

Verbs:

* ``index check [TOOL]`` — run the conformance gate for one tool (or all) and
  report each verdict. Read-only.
* ``index build [--out DIR]`` — emit ``catalog.json`` + the static PEP 503
  ``/simple/`` tree for the conformant tools (the artifacts the site renders
  from).
* ``index overview`` — describe this noun's surface (required: a noun with
  action-verbs must expose ``overview``).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from culture_tools.cli._commands.overview import emit_overview
from culture_tools.cli._errors import EXIT_ENV_ERROR, EXIT_USER_ERROR, CliError
from culture_tools.cli._output import emit_diagnostic, emit_result
from culture_tools.index import build, check_all, check_named
from culture_tools.index._conformance import auditor_available

_DEFAULT_OUT = "build/index"

_VERBS = [
    "index check [TOOL] — run the AgentFront conformance gate (all tools, or one)",
    "index build [--out DIR] — emit catalog.json + the static PEP 503 /simple/ tree",
    "index overview — describe the index surface (this command)",
]


def _index_sections() -> list[dict[str, object]]:
    return [
        {"title": "Verbs", "items": list(_VERBS)},
        {
            "title": "Membership rule",
            "items": [
                "a tool is listed iff `agentfront cli doctor <repo> --strict` is healthy",
                "the gate is delegated, never reimplemented (agentfront is the authority)",
                "non-conformant candidates are reported and excluded, not silently dropped",
            ],
        },
        {
            "title": "Artifacts (index build)",
            "items": [
                "catalog.json — the catalog the site renders from (conformant + excluded)",
                "simple/ — static PEP 503 tree; pages link out to each tool's PyPI files",
            ],
        },
    ]


def cmd_index_overview(args: argparse.Namespace) -> int:
    emit_overview(
        "culture-tools index",
        _index_sections(),
        json_mode=bool(getattr(args, "json", False)),
    )
    return 0


def cmd_index_check(args: argparse.Namespace) -> int:
    json_mode = bool(getattr(args, "json", False))
    if not auditor_available():
        raise CliError(
            code=EXIT_ENV_ERROR,
            message="agentfront (the conformance auditor) is not on PATH",
            remediation="install it with: uv tool install agentfront",
        )

    name = getattr(args, "tool", None)
    if name:
        verdict = check_named(name)
        if verdict is None:
            raise CliError(
                code=EXIT_USER_ERROR,
                message=f"no candidate tool named '{name}' in the manifest",
                remediation="list candidates with: culture-tools index check",
            )
        verdicts = [verdict]
    else:
        verdicts = check_all()

    if json_mode:
        emit_result({"verdicts": [v.to_dict() for v in verdicts]}, json_mode=True)
        return 0

    lines = ["culture-tools index — conformance", ""]
    for v in verdicts:
        if not v.ran:
            mark, detail = "skip", f"could not run: {v.error}"
        elif v.healthy:
            mark, detail = "ok", "AgentFront-conformant"
        else:
            failed = ", ".join(v.failing_bundles) or "see agentfront cli doctor"
            mark, detail = "FAIL", f"failing bundles: {failed}"
        lines.append(f"[{mark}] {v.tool}: {detail}")
    listed = sum(1 for v in verdicts if v.ran and v.healthy)
    lines += ["", f"{listed}/{len(verdicts)} candidate(s) conformant → listed"]
    emit_result("\n".join(lines), json_mode=False)
    return 0


def cmd_index_build(args: argparse.Namespace) -> int:
    json_mode = bool(getattr(args, "json", False))
    if not auditor_available():
        raise CliError(
            code=EXIT_ENV_ERROR,
            message="agentfront (the conformance auditor) is not on PATH",
            remediation="install it with: uv tool install agentfront",
        )
    out_dir = Path(getattr(args, "out", None) or _DEFAULT_OUT)
    # In --json mode both streams must stay structured; skip the plain
    # progress line so stderr carries nothing a JSON consumer can't parse.
    if not json_mode:
        emit_diagnostic(f"building index into {out_dir} …")
    summary = build(out_dir)

    if json_mode:
        emit_result(summary, json_mode=True)
        return 0
    text = (
        f"culture-tools index build\n\n"
        f"  catalog : {summary['catalog']}\n"
        f"  simple  : {summary['simple']}\n"
        f"  listed  : {summary['listed']}/{summary['candidates']} conformant\n"
        f"  excluded: {summary['excluded']}"
    )
    emit_result(text, json_mode=False)
    return 0


def _no_verb(args: argparse.Namespace) -> int:
    return cmd_index_overview(args)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "index",
        help="Certify/catalog agent-first tools (see 'culture-tools index overview').",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=_no_verb, json=False)
    # parser_class propagates from the top-level subparsers so nested parse errors
    # route through the structured error contract (error:/hint: + exit 1).
    noun_sub = p.add_subparsers(dest="index_command", parser_class=type(p))

    ov = noun_sub.add_parser("overview", help="Describe the culture-tools index surface.")
    ov.add_argument("--json", action="store_true", help="Emit structured JSON.")
    ov.set_defaults(func=cmd_index_overview)

    ck = noun_sub.add_parser(
        "check",
        help="Run the AgentFront conformance gate (all candidates, or one TOOL).",
    )
    ck.add_argument("tool", nargs="?", help="Candidate name; omit to check all.")
    ck.add_argument("--json", action="store_true", help="Emit structured JSON.")
    ck.set_defaults(func=cmd_index_check)

    bd = noun_sub.add_parser(
        "build",
        help="Emit catalog.json + the static PEP 503 /simple/ tree for conformant tools.",
    )
    bd.add_argument(
        "--out",
        default=_DEFAULT_OUT,
        help=f"Output directory (default: {_DEFAULT_OUT}).",
    )
    bd.add_argument("--json", action="store_true", help="Emit structured JSON.")
    bd.set_defaults(func=cmd_index_build)
