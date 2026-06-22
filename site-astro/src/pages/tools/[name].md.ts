// /tools/<name>.md — the markdown twin of each tool's detail page, for agents
// that prefer raw markdown over HTML.
import type { APIRoute, GetStaticPaths } from 'astro';
import { tools } from '../../data/catalog.ts';
import type { Tool } from '../../data/catalog.ts';

export const getStaticPaths: GetStaticPaths = () =>
  tools.map((tool) => ({ params: { name: tool.name }, props: { tool } }));

export const GET: APIRoute = ({ props, site }) => {
  const tool = props.tool as Tool;
  const base = (site?.toString() ?? 'https://tools.culture.dev/').replace(/\/$/, '');
  const lines: string[] = [];

  lines.push(`# ${tool.name}`);
  lines.push('');
  lines.push(`> ${tool.summary || tool.purpose || ''}`);
  lines.push('');
  lines.push(`- **Version:** ${tool.version || '—'}`);
  lines.push(`- **Install:** \`${tool.install}\``);
  lines.push(`- **Backend:** ${tool.backend || 'unknown'}`);
  lines.push(`- **Repository:** https://github.com/${tool.repo}`);
  lines.push(`- **PyPI:** https://pypi.org/project/${tool.pypi}/`);
  lines.push('- **Conformance:** AgentFront-certified (`agentfront cli doctor --strict`)');
  lines.push('');

  if (tool.purpose && tool.purpose !== tool.summary) {
    lines.push(tool.purpose);
    lines.push('');
  }

  if (tool.commands.length) {
    lines.push('## Command surface');
    lines.push('');
    for (const c of tool.commands) {
      lines.push(`- \`${tool.name} ${c.path.join(' ')}\` — ${c.summary}`);
    }
    lines.push('');
  }

  lines.push(`[← the full index](${base}/llms.txt)`);
  lines.push('');

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  });
};
