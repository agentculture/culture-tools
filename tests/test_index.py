"""Tests for the index noun and the AgentFront conformance gate.

The gate is exercised with an injected command runner so nothing shells out to
``agentfront``; the CLI wiring (overview, explain, structured errors) is checked
end-to-end through ``main``.
"""

from __future__ import annotations

import json

import pytest

from culture_tools.cli import main
from culture_tools.index import build, check_all, check_named
from culture_tools.index._catalog import build_catalog, build_entry
from culture_tools.index._conformance import (
    CommandResult,
    Verdict,
    gate,
    parse_verdict,
)
from culture_tools.index._introspect import ToolMeta
from culture_tools.index._manifest import Tool, candidates, find
from culture_tools.index._simple import normalize, pypi_links, render_project, render_root

# --- conformance parsing --------------------------------------------------


def _doctor_json(*, healthy: bool, checks: list[dict] | None = None) -> str:
    return json.dumps({"tool": "x", "healthy": healthy, "checks": checks or []})


def test_parse_verdict_healthy() -> None:
    res = CommandResult(0, _doctor_json(healthy=True), "")
    v = parse_verdict("agentfront", res)
    assert v.healthy is True
    assert v.ran is True
    assert v.failing_bundles == ()


def test_parse_verdict_collects_failing_bundles() -> None:
    checks = [
        {"bundle": "json", "passed": False},
        {"bundle": "errors", "passed": False},
        {"bundle": "structure", "passed": True},
        {"bundle": "json", "passed": False},  # dup bundle collapses
    ]
    res = CommandResult(1, _doctor_json(healthy=False, checks=checks), "")
    v = parse_verdict("toy", res)
    assert v.healthy is False
    assert v.failing_bundles == ("errors", "json")  # sorted + deduped


def test_parse_verdict_unparseable_is_an_error_not_a_failure() -> None:
    res = CommandResult(2, "not json", "boom")
    v = parse_verdict("toy", res)
    assert v.healthy is False
    assert v.ran is False
    assert "could not parse" in v.error


def test_gate_passes_strict_flag_and_uses_injected_runner() -> None:
    seen: list[list[str]] = []

    def runner(cmd):
        seen.append(list(cmd))
        return CommandResult(0, _doctor_json(healthy=True), "")

    v = gate("/some/repo", tool="toy", runner=runner)
    assert v.healthy is True
    assert seen == [["agentfront", "cli", "doctor", "/some/repo", "--json", "--strict"]]


# --- manifest + aggregate -------------------------------------------------


def test_manifest_is_non_empty_and_named() -> None:
    names = [t.name for t in candidates()]
    assert "agentfront" in names
    assert "culture-tools" in names
    assert find("culture-tools") is not None
    assert find("does-not-exist") is None


def test_check_all_runs_every_candidate() -> None:
    runner = lambda cmd: CommandResult(0, _doctor_json(healthy=True), "")  # noqa: E731
    verdicts = check_all(runner=runner)
    assert len(verdicts) == len(candidates())
    assert all(isinstance(v, Verdict) and v.healthy for v in verdicts)


def test_check_named_unknown_returns_none() -> None:
    assert check_named("nope", runner=lambda cmd: CommandResult(0, "{}", "")) is None


# --- CLI wiring -----------------------------------------------------------


def test_index_overview_text(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["index", "overview"])
    assert rc == 0
    assert "# culture-tools index" in capsys.readouterr().out


def test_index_overview_json_shape(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["index", "overview", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["subject"] == "culture-tools index"
    assert isinstance(payload["sections"], list)


def test_index_bare_is_non_empty(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["index"])
    assert rc == 0
    assert capsys.readouterr().out.strip()


def test_index_check_unknown_flag_structured_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["index", "check", "--bogus"])
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert err.startswith("error:")
    assert "hint:" in err


def test_index_explain_resolves(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["explain", "index", "check"])
    assert rc == 0
    assert "# culture-tools index" in capsys.readouterr().out


def test_index_check_unknown_tool_is_user_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # An unknown manifest name is bad *user input* → exit 1, not the env-error 2.
    monkeypatch.setattr("culture_tools.cli._commands.index.auditor_available", lambda: True)
    rc = main(["index", "check", "no-such-tool"])
    assert rc == 1  # EXIT_USER_ERROR
    err = capsys.readouterr().err
    assert err.startswith("error:")
    assert "no candidate tool" in err


def test_index_build_diagnostic_respects_json_mode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = {
        "out": "o",
        "catalog": "c",
        "simple": "s",
        "listed": 1,
        "excluded": 0,
        "candidates": 1,
    }
    monkeypatch.setattr("culture_tools.cli._commands.index.auditor_available", lambda: True)
    monkeypatch.setattr("culture_tools.cli._commands.index.build", lambda out_dir, **kw: fake)

    # text mode: the human progress line lands on stderr
    assert main(["index", "build"]) == 0
    cap = capsys.readouterr()
    assert "building index" in cap.err

    # --json mode: stderr stays clean, stdout is a single JSON object
    assert main(["index", "build", "--json"]) == 0
    cap = capsys.readouterr()
    assert cap.err == ""
    assert json.loads(cap.out) == fake


def test_learn_json_advertises_every_index_verb() -> None:
    from culture_tools.cli._commands.learn import _as_json_payload

    paths = {tuple(c["path"]) for c in _as_json_payload()["commands"]}
    assert {("index", "check"), ("index", "build"), ("index", "overview")} <= paths


# --- PEP 503 emitter (pure) -----------------------------------------------


def test_normalize_pep503() -> None:
    assert normalize("Culture_Tools") == "culture-tools"
    assert normalize("agent..front") == "agent-front"
    assert normalize("a_-_b") == "a-b"


def test_render_root_lists_sorted_normalized_anchors() -> None:
    html = render_root(["zeta", "Alpha_one", "beta"])
    assert html.index("alpha-one/") < html.index("beta/") < html.index("zeta/")
    assert 'href="alpha-one/"' in html
    assert ">Alpha_one<" in html  # display name escaped, href normalized


def test_render_root_empty_is_valid() -> None:
    html = render_root([])
    assert "<!DOCTYPE html>" in html
    assert "no conformant tools" in html


def test_render_project_lists_links() -> None:
    html = render_project("agtag", pypi_links("agtag"), note="hi")
    assert "Links for agtag" in html
    assert "https://pypi.org/project/agtag/" in html
    assert "<!-- hi -->" in html


# --- catalog assembly (pure) ----------------------------------------------


def test_build_entry_shape() -> None:
    tool = Tool("agtag", "agtag", "agtag", "agentculture/agtag", "agtag")
    meta = ToolMeta(version="1.2.3", summary="tag things", backend="claude", purpose="P")
    entry = build_entry(tool, meta)
    assert entry["name"] == "agtag"
    assert entry["version"] == "1.2.3"
    assert entry["install"] == "uv tool install agtag"
    assert entry["conformant"] is True
    assert entry["homepage"] == "https://github.com/agentculture/agtag"  # fallback


def test_build_catalog_sorts_and_counts() -> None:
    e1 = {"name": "zed"}
    e2 = {"name": "abe"}
    cat = build_catalog(generator_version="9.9", entries=[e1, e2], excluded=[])
    assert cat["count"] == 2
    assert [t["name"] for t in cat["tools"]] == ["abe", "zed"]
    assert cat["contract"] == "agentfront cli doctor --strict"
    assert cat["generated_with"] == "culture-tools 9.9"


# --- build() end-to-end (hermetic: fake manifest + temp repos + runner) ---


def _fake_repo(repos_dir, name, *, version="0.1.0", backend="colleague"):
    repo = repos_dir / name
    repo.mkdir(parents=True)
    (repo / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "{version}"\n'
        f'description = "the {name} tool"\n'
        f'[project.urls]\nHomepage = "https://example.test/{name}"\n',
        encoding="utf-8",
    )
    (repo / "culture.yaml").write_text(
        f"agents:\n- suffix: {name}\n  backend: {backend}\n  model: m1\n", encoding="utf-8"
    )
    return repo


def _runner_factory(healthy_names):
    def runner(cmd):
        cmd = list(cmd)
        if cmd[:3] == ["agentfront", "cli", "doctor"]:
            repo = cmd[3]
            healthy = any(repo.endswith(n) for n in healthy_names)
            checks = [] if healthy else [{"bundle": "json", "passed": False}]
            return CommandResult(0, json.dumps({"healthy": healthy, "checks": checks}), "")
        if cmd[1:3] == ["learn", "--json"]:
            return CommandResult(0, json.dumps({"purpose": f"purpose of {cmd[0]}"}), "")
        return CommandResult(1, "", "unexpected")

    return runner


def test_build_emits_catalog_and_simple_tree(tmp_path) -> None:
    repos = tmp_path / "repos"
    repos.mkdir()
    _fake_repo(repos, "good-one")
    _fake_repo(repos, "bad-one")
    tools = (
        Tool("good-one", "good-one", "good-one", "agentculture/good-one", "good-one"),
        Tool("bad-one", "bad-one", "bad-one", "agentculture/bad-one", "bad-one"),
    )
    out = tmp_path / "out"

    summary = build(out, tools=tools, repos_dir=repos, runner=_runner_factory({"good-one"}))

    assert summary["listed"] == 1
    assert summary["excluded"] == 1
    assert summary["candidates"] == 2

    catalog = json.loads((out / "catalog.json").read_text())
    assert catalog["count"] == 1
    assert catalog["tools"][0]["name"] == "good-one"
    assert catalog["tools"][0]["purpose"] == "purpose of good-one"
    assert catalog["tools"][0]["version"] == "0.1.0"
    assert catalog["tools"][0]["backend"] == "colleague"
    assert [e["name"] for e in catalog["excluded"]] == ["bad-one"]
    assert catalog["excluded"][0]["failing_bundles"] == ["json"]

    root = (out / "simple" / "index.html").read_text()
    assert 'href="good-one/"' in root
    assert "bad-one" not in root  # excluded → no simple page
    assert (out / "simple" / "good-one" / "index.html").is_file()
    assert not (out / "simple" / "bad-one").exists()
