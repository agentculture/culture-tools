# site-astro — tools.culture.dev

The public index site for **tools.culture.dev**: a catalog of agent-first CLI
tools, each certified against the AgentFront contract. Astro, fully static
(`output: 'static'`, no adapter), so `astro build` emits a `dist/` that
Cloudflare Pages serves directly (M3).

## Data flow

The site renders from a single generated file, `src/data/catalog.json`, produced
by the M1 generator in the parent package:

```text
culture-tools index build  ──►  catalog.json   ──►  src/data/   (imported, typed)
                           └─►  simple/         ──►  public/simple/   (static PEP 503)
```

`scripts/sync-catalog.sh` runs the generator and distributes both artifacts.
Every tool in `catalog.json` passed `agentfront cli doctor <repo> --strict`;
the `excluded` roster records the candidates that did not.

## Develop

```bash
npm install
npm run catalog     # regenerate src/data/catalog.json + public/simple/ (needs uv + agentfront)
npm run dev         # http://localhost:4321
npm run build       # -> dist/
npm run preview
```

`catalog.json` is committed so the site builds without the Python toolchain;
`npm run catalog` refreshes it against live conformance.

## Layout

- `src/data/catalog.ts` — typed view over `catalog.json`.
- `src/layouts/Base.astro` — HTML shell, fonts, theme toggle (light cream default).
- `src/components/` — `ToolCard`, `ConformanceBadge`, header, footer.
- `src/pages/index.astro` — hero + certified-tool grid + roadmap of pending candidates.
- `src/pages/tools/[name].astro` — per-tool detail (install, links, command surface).

## Theme

Anthropic-cream, light by default (warm `#FFFAF5`, clay accent `#D97706`), with a
dark mirror. Palette matches the sibling `agentic-human` / `humanic-ai` sites.
