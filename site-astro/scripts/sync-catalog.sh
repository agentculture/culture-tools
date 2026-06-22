#!/usr/bin/env bash
# Regenerate the catalog the site renders from.
#
# Runs the M1 generator (`culture-tools index build`) and distributes its two
# artifacts into the Astro tree:
#
#   catalog.json -> src/data/        (imported at build time, typed via catalog.ts)
#   simple/      -> public/simple/   (served verbatim as the static PEP 503 index)
#
# Run this before `npm run build` whenever a tool's conformance or metadata
# changes. In CI (M3) it runs as the pre-build step so the deployed catalog is
# always freshly certified.
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"   # site-astro/
repo="$(cd "$here/.." && pwd)"             # culture-tools/
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

( cd "$repo" && uv run culture-tools index build --out "$stage" )

cp "$stage/catalog.json" "$here/src/data/catalog.json"
rm -rf "$here/public/simple"
cp -r "$stage/simple" "$here/public/simple"

echo "synced: src/data/catalog.json + public/simple/ (from culture-tools index build)"
