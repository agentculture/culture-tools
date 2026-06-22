// /llms.txt — the agent-facing index (the emerging llms.txt convention: like a
// sitemap, but for LLMs). Built from the catalog so it stays in sync.
import type { APIRoute } from 'astro';
import { tools, excluded, catalog } from '../data/catalog.ts';

const DESC =
  'The package index for agent-first CLI tools — every listing certified against ' +
  'the AgentFront contract (`agentfront cli doctor --strict`).';

export const GET: APIRoute = ({ site }) => {
  const base = (site?.toString() ?? 'https://tools.culture.dev/').replace(/\/$/, '');
  const lines: string[] = [];

  lines.push('# tools.culture.dev');
  lines.push('');
  lines.push(`> ${DESC}`);
  lines.push('');
  lines.push(
    'Each tool has a markdown twin — append `.md` to its page URL ' +
      `(e.g. ${base}/tools/agentfront.md). The full catalog as JSON is at ` +
      `${base}/catalog.json. Certified tools are pip-installable: ` +
      `\`pip install --index-url ${base}/simple/ <tool>\`.`,
  );
  lines.push('');

  lines.push('## Certified tools');
  lines.push('');
  for (const t of tools) {
    const summary = t.summary || t.purpose || '';
    lines.push(`- [${t.name}](${base}/tools/${t.name}.md) — ${summary} (v${t.version}; \`${t.install}\`)`);
  }
  lines.push('');

  if (excluded.length) {
    lines.push('## Candidates not yet conformant');
    lines.push('');
    for (const e of excluded) {
      const why = e.ran ? `needs: ${e.failing_bundles.join(', ')}` : `could not run: ${e.error}`;
      lines.push(`- ${e.name} — ${why}`);
    }
    lines.push('');
  }

  lines.push(`Generated with ${catalog.generated_with} · gate: ${catalog.contract}`);
  lines.push('');

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
