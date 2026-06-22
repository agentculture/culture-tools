// /index.md — the markdown twin of the landing page.
import type { APIRoute } from 'astro';
import { tools, excluded, catalog } from '../data/catalog.ts';

export const GET: APIRoute = ({ site }) => {
  const base = (site?.toString() ?? 'https://tools.culture.dev/').replace(/\/$/, '');
  const lines: string[] = [];

  lines.push('# tools.culture.dev');
  lines.push('');
  lines.push(
    '> The index for agent-first CLI tools — every listing certified against the ' +
      'AgentFront contract.',
  );
  lines.push('');
  lines.push(
    `Install a certified tool: \`pip install --index-url ${base}/simple/ <tool>\` ` +
      'or `uv tool install <tool>`.',
  );
  lines.push('');

  lines.push('## Certified tools');
  lines.push('');
  for (const t of tools) {
    lines.push(
      `- **${t.name}** (v${t.version}) — ${t.summary || t.purpose} — ` +
        `\`${t.install}\` — ${base}/tools/${t.name}.md`,
    );
  }
  lines.push('');

  if (excluded.length) {
    lines.push('## Not yet conformant');
    lines.push('');
    for (const e of excluded) {
      const why = e.ran ? `needs: ${e.failing_bundles.join(', ')}` : `error: ${e.error}`;
      lines.push(`- ${e.name} — ${why}`);
    }
    lines.push('');
  }

  lines.push(`Generated with ${catalog.generated_with} · gate: ${catalog.contract}`);
  lines.push('');

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  });
};
