// Typed view over the generated catalog.
//
// `catalog.json` is produced by `culture-tools index build` (see
// scripts/sync-catalog.sh). Every tool in `tools` passed the membership gate —
// `agentfront cli doctor <repo> --strict` reported healthy — and `excluded`
// records the candidates that did not, with the bundles they failed. Do not
// hand-edit catalog.json; regenerate it with `npm run catalog`.
import catalogJson from './catalog.json';

export interface ToolCommand {
  path: string[];
  summary: string;
}

export interface Tool {
  name: string;
  pypi: string;
  repo: string;
  homepage: string;
  version: string;
  summary: string;
  purpose: string;
  backend: string;
  model: string;
  commands: ToolCommand[];
  install: string;
  conformant: boolean;
}

export interface ExcludedTool {
  name: string;
  ran: boolean;
  failing_bundles: string[];
  error: string;
}

export interface Catalog {
  generated_with: string;
  contract: string;
  count: number;
  tools: Tool[];
  excluded: ExcludedTool[];
}

export const catalog = catalogJson as unknown as Catalog;
export const tools: Tool[] = catalog.tools;
export const excluded: ExcludedTool[] = catalog.excluded;

export function toolByName(name: string): Tool | undefined {
  return tools.find((tool) => tool.name === name);
}
