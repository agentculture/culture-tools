# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`culture-tools` is the agent that backs **tools.culture.dev** — the package index
for agent-first CLI tools that conform to the `agentfront` contract. Today the
repo is the **canonical clonable scaffold** (the former `culture-agent-template`):
an agent-first CLI, a mesh identity, the guildmaster skill kit, and a build/deploy
baseline. The site/index itself is being built out (see "Site build" below); the
Python package is the reference an agent clones to mint a new mesh agent.

The runtime package has **zero third-party dependencies** (`dependencies = []` in
`pyproject.toml`). This is a hard constraint — `whoami`/`doctor` parse
`culture.yaml` by hand rather than import a YAML library. Do not add a runtime
dependency without an explicit decision to drop the zero-dep property; dev-only
tools belong in `[dependency-groups].dev`.

### Identity, not a name you can assume

This agent runs `backend: colleague` (see `culture.yaml`), so its **resident
prompt file is `AGENTS.colleague.md`**, not `CLAUDE.md`. `CLAUDE.md` (this file)
guides Claude Code working *in* the repo; `AGENTS.colleague.md` is the prompt the
colleague mesh resident loads. `doctor` enforces this mapping
(`colleague → AGENTS.colleague.md`); a backend change in `culture.yaml` that isn't
taught to `doctor` will fail the `backend-consistency` invariant.

## Commands

All Python work goes through **uv**. Python 3.12+ required.

```bash
uv sync                                       # install deps (incl. dev group)
uv run pytest -n auto                         # full test suite (xdist parallel)
uv run pytest tests/test_cli.py::test_whoami_text   # a single test
uv run pytest -k doctor                        # tests matching a name
uv run culture-tools <verb>                    # run the CLI (whoami, learn, …)
```

Lint (CI runs each of these; all must pass):

```bash
uv run black --check culture_tools tests
uv run isort --check-only culture_tools tests
uv run flake8 culture_tools tests
uv run bandit -c pyproject.toml -r culture_tools
markdownlint-cli2 "**/*.md" "#node_modules" "#.local" "#.claude/skills" "#.teken"
uv run teken cli doctor . --strict            # the agent-first rubric gate
```

`teken cli doctor . --strict` is the **agent-first rubric gate** and is the
non-obvious one: it is a CI-blocking check (`teken`, the `afi-cli`, is a dev
dependency) that audits the CLI for the `agentfront` contract. Several design
choices exist only to satisfy it — see "The rubric shapes the code" below. Run it
locally before pushing; a green pytest run does not imply a green rubric.

## Architecture

### The CLI is a registry of `register()`-ing command modules

`culture_tools/cli/__init__.py` owns `main()` and `_build_parser()`. Each verb or
noun group is a module under `culture_tools/cli/_commands/` exposing a
`register(subparsers)` function; `_build_parser()` calls them in turn. To add a
command, write a `_commands/<name>.py` with `register()` and a `cmd_*` handler,
then add one `register()` call in `_build_parser()` (there's a marked spot for it).

Global verbs (not nested under a noun): `whoami`, `learn`, `explain`, `overview`,
`doctor`. Noun groups (e.g. `cli`) nest their own subparsers. `explain` is global
and path-addressable — `explain cli overview` resolves a tuple key, distinct from
`--help`.

### Three stable contracts every command obeys

These are load-bearing; tests and the rubric enforce them. Match them in new code.

1. **stdout vs stderr split** (`cli/_output.py`). Results → stdout; errors and
   human diagnostics → stderr; **never mixed**. In `--json` mode both streams
   carry JSON to their respective destinations. Use `emit_result` /
   `emit_error` / `emit_diagnostic` — don't `print`.

2. **Structured errors via `CliError`** (`cli/_errors.py`). Every failure raises
   `CliError(code, message, remediation)`. `_dispatch()` in `cli/__init__.py`
   catches it, routes through `emit_error`, and returns the code; it also wraps
   *any* unexpected exception so **no Python traceback ever leaks to stderr**.
   Even argparse parse errors are routed: `_CliArgumentParser` overrides
   `.error()`, and because the subparsers are built with
   `parser_class=_CliArgumentParser`, nested parse errors get the same
   `error:` / `hint:` shape and exit 1 (not argparse's default exit 2). JSON mode
   for parse-time errors works via a class-level `_json_hint` that `main()`
   pre-populates by scanning raw argv for `--json` (because `args.json` doesn't
   exist yet when parsing fails).

3. **Exit-code policy.** `0` success · `1` user-input error · `2` environment
   error · `3+` reserved. Defined once in `cli/_errors.py`; documented in `learn`.

Every command also accepts `--json`.

### `explain` catalog

`culture_tools/explain/catalog.py` holds verbatim markdown keyed by command-path
tuples (`("cli", "overview")`). `explain/__init__.py:resolve()` looks the path up
or raises `CliError`. **Invariant enforced by a test**
(`test_every_catalog_path_resolves`): every key in `ENTRIES` must resolve. When
you add a command, add its catalog entry too.

### Identity probe (`whoami`) and `doctor`

`whoami.py:find_culture_yaml()` walks up from `__file__` (not the CWD) to find the
agent's *own* `culture.yaml`, and `read_agent_fields()` hand-parses the first
agent block (zero-dep rule). A wheel install ships no `culture.yaml`, so both
fall back to literal defaults — code paths must tolerate that. `doctor.py` mirrors
the two invariants `steward doctor` checks (`prompt-file-present`,
`backend-consistency`) plus a `skills-present` check, and reports the
rubric-shaped `{healthy, checks: [{id, passed, severity, message, remediation}]}`.

### The rubric shapes the code

Some constructs exist *only* to pass `teken cli doctor . --strict`, and look
redundant otherwise — don't "simplify" them away:

- The `cli` noun group exists so the rubric's `overview_cli_noun_exists` check
  passes (any noun with action-verbs must expose `overview`). `cli overview`
  describes the CLI surface; the global `overview` describes the agent.
- `learn` must be ≥200 chars and mention purpose, command map, exit codes,
  `--json`, and `explain` (`test_learn_text` guards this).
- Descriptive verbs (`overview`) must **not** hard-fail on a bad target path —
  `overview` takes an ignored optional `target` so a stray path still exits 0.

## Conventions (non-obvious, enforced)

- **Version-bump every PR.** The `version-check` CI job fails any PR whose
  `pyproject.toml` version equals `main`'s — even docs/CI-only changes. Use the
  `version-bump` skill (or `/version-bump patch|minor|major`); it updates
  `pyproject.toml` and prepends a Keep-a-Changelog entry to `CHANGELOG.md`.
- **SonarCloud coverage needs repo-relative paths.** `[tool.coverage.run]
  relative_files = true` is set so `coverage.xml` filenames map onto
  `sonar.sources=culture_tools`; without it Sonar silently reports 0% coverage.
  Coverage gate: `fail_under = 60`. The Sonar quality gate (`sonar.qualitygate.wait`)
  blocks merge, but the scan step is a no-op without `SONAR_TOKEN` (fork PRs).
- **Skills are cite-don't-import vendored**, not authored here. `.claude/skills/`
  comes from **guildmaster** (the skills supplier); `docs/skill-sources.md` is the
  provenance ledger and re-sync procedure. Don't edit vendored script bodies —
  lift changes upstream into guildmaster and re-vendor. Two tracked local
  divergences exist (`agex`→`devex`, `outsource`→`ask-colleague`); read that doc
  before touching a skill. Every vendored `SKILL.md` must carry `type: command`
  (load-bearing: `core.skill_loader` silently skips files without it).
- **PR lane = the `cicd` skill** (layered on `devex pr`): `cicd open`, `cicd read`,
  `cicd reply`, plus `cicd status` (SonarCloud gate + unresolved threads) and
  `cicd await` (poll until CI settles, non-zero on red gate). Requires `devex`
  (>=0.21) on PATH. PR-reply signatures resolve the nick from `culture.yaml` via
  `_resolve-nick.sh` — don't sign PR bodies the cicd scripts author.

## Renaming the template

This repo is meant to be cloned and renamed. The name `culture-tools` /
`culture_tools` / `culture.tools.dev` is hard-coded in ~100 places (package dir,
`pyproject.toml` dist+script+coverage+isort, `sonar-project.properties`
projectKey, `culture.yaml` suffix, README, `explain` catalog strings, the
`_ISSUES_URL`, the `_FALLBACK_NICK`, tests). Discover every occurrence before
editing:

```bash
git grep -n -i -e 'culture-tools' -e 'culture_tools'
git ls-files | grep -i culture_tools     # the package directory itself
```

Then update `culture.yaml` (`suffix`/`backend`), rewrite `CLAUDE.md` and
`AGENTS.colleague.md` (or the backend's prompt file) for the new agent, and
re-vendor only the skills you need (`docs/skill-sources.md`).

## Site build (tools.culture.dev)

The public index site lives under **`site-astro/`** — an Astro 6 static site
(`output: 'static'`, no adapter, so `astro build` emits a pure-static `dist/`
for Cloudflare Pages). Architecture of record: `docs/design/tools-culture-dev.md`.

**The site renders from one generated file**, `site-astro/src/data/catalog.json`,
produced by the M1 generator in this package (`culture-tools index build`). The
data flow is one-way:

```text
culture-tools index build  →  catalog.json  →  src/data/      (imported, typed via catalog.ts)
                           →  simple/        →  public/simple/  (static PEP 503, served verbatim)
```

`site-astro/scripts/sync-catalog.sh` (`npm run catalog`) runs the generator and
distributes both artifacts. `catalog.json` + `public/simple/` are **committed**
so the site builds without the Python toolchain; regenerate them against live
conformance with `npm run catalog` before a deploy. Don't hand-edit
`catalog.json` — every entry passed `agentfront cli doctor <repo> --strict`.

Site commands (run inside `site-astro/`): `npm install`, `npm run dev`
(localhost:4321), `npm run build`, `npm run check` (astro type-check),
`npm run catalog` (refresh the data).

**Theme:** Anthropic-cream, light by default (warm `#FFFAF5`, clay accent
`#D97706`) with a dark mirror — palette aligned with the sibling
`../agentic-human` / `../humanic-ai` sites. The katvan / auntiepypi / cultureflare
siblings supplied the static-Astro structure, the PEP 503 emitter, and the
Cloudflare deploy path respectively; consult them before extending site infra.
M3 (Cloudflare deploy lane) and M4 (llms.txt, markdown twins, S3 durable tier)
are still ahead — see the design doc's milestones.
