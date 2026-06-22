"""Guard: the committed site catalog must not drift from the package version.

``site-astro/src/data/catalog.json`` is a *generated* artifact (produced by
``culture-tools index build``) that is committed so the Astro site builds without
the Python toolchain. Because it is committed, it can silently go stale when
``pyproject.toml``'s version bumps without a ``npm run catalog`` re-sync — Qodo
flagged exactly this drift on PR #3 (catalog said ``0.4.0`` while the package was
``0.5.0``).

This test reads the *committed* files only (no regeneration, so it needs neither
``uv`` nor ``agentfront`` in CI) and fails when the catalog's ``culture-tools``
entry — or its ``generated_with`` stamp — lags ``pyproject``'s version. The remedy
is always the same: ``cd site-astro && npm run catalog`` and recommit.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_CATALOG = _REPO / "site-astro" / "src" / "data" / "catalog.json"
_REMEDY = "regenerate with `cd site-astro && npm run catalog` and recommit"


def _pyproject_version() -> str:
    data = tomllib.loads((_REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


@pytest.mark.skipif(not _CATALOG.is_file(), reason="site catalog not present")
def test_committed_catalog_matches_package_version() -> None:
    version = _pyproject_version()
    catalog = json.loads(_CATALOG.read_text(encoding="utf-8"))

    assert catalog["generated_with"] == f"culture-tools {version}", (
        f"catalog.json generated_with={catalog['generated_with']!r} but pyproject "
        f"is {version!r} — stale catalog; {_REMEDY}."
    )

    entry = next((t for t in catalog["tools"] if t["name"] == "culture-tools"), None)
    assert entry is not None, (
        "culture-tools is missing from its own catalog (excluded by the gate?) — "
        f"investigate, then {_REMEDY}."
    )
    assert entry["version"] == version, (
        f"catalog culture-tools entry is {entry['version']!r} but pyproject is "
        f"{version!r} — stale catalog; {_REMEDY}."
    )
