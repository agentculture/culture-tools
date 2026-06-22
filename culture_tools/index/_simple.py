"""Static PEP 503 ``/simple/`` emitter.

Pure string builders — no I/O, no deps — so they unit-test cleanly. Ported from
``../auntiepypi``'s index logic (PEP 503 name normalization + the root/project
HTML), adapted to emit *static* files at build time rather than serve them from a
running ``http.server``.

v1 does not host wheels: each project page links out to the tool's canonical PyPI
distribution page. The pip-resolvable ``/simple/<name>/`` → PyPI proxy is a
deploy-layer concern (a Cloudflare ``_redirects`` rule), handled in M3.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

_NORMALIZE_RE = re.compile(r"[-_.]+")


def normalize(name: str) -> str:
    """PEP 503 normalized project name: lowercase, runs of ``[-_.]`` → single ``-``."""
    return _NORMALIZE_RE.sub("-", name).lower()


@dataclass(frozen=True)
class DistLink:
    """One anchor on a project page (a distribution file, or a PyPI pointer)."""

    label: str
    href: str


def render_root(project_names: list[str]) -> str:
    """The ``/simple/index.html`` root: one anchor per project, sorted, normalized."""
    rows = [
        f'    <a href="{normalize(name)}/">{html.escape(name)}</a><br/>'
        for name in sorted(project_names, key=normalize)
    ]
    body = "\n".join(rows) if rows else "    <!-- no conformant tools -->"
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="utf-8" />\n'
        '    <meta name="pypi:repository-version" content="1.0" />\n'
        "    <title>Simple index — tools.culture.dev</title>\n"
        "  </head>\n"
        "  <body>\n"
        f"{body}\n"
        "  </body>\n"
        "</html>\n"
    )


def render_project(name: str, links: list[DistLink], *, note: str = "") -> str:
    """A ``/simple/<name>/index.html`` page listing distribution anchors."""
    rows = [
        f'    <a href="{html.escape(link.href)}">{html.escape(link.label)}</a><br/>'
        for link in links
    ]
    body = "\n".join(rows) if rows else "    <!-- no distributions -->"
    note_html = f"    <!-- {html.escape(note)} -->\n" if note else ""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="utf-8" />\n'
        '    <meta name="pypi:repository-version" content="1.0" />\n'
        f"    <title>Links for {html.escape(name)}</title>\n"
        "  </head>\n"
        "  <body>\n"
        f"    <h1>Links for {html.escape(name)}</h1>\n"
        f"{note_html}"
        f"{body}\n"
        "  </body>\n"
        "</html>\n"
    )


def pypi_links(pypi_name: str) -> list[DistLink]:
    """v1 project-page links: point at the tool's canonical PyPI home."""
    return [
        DistLink(f"{pypi_name} on PyPI", f"https://pypi.org/project/{pypi_name}/"),
        DistLink(
            "PyPI simple index (installable files)",
            f"https://pypi.org/simple/{normalize(pypi_name)}/",
        ),
    ]
