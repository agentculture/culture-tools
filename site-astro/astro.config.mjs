// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// tools.culture.dev — the package index for agent-first CLI tools.
//
// output: 'static' with NO adapter => `astro build` emits a fully static dist/
// (HTML + assets, zero server runtime). That is exactly what Cloudflare Pages
// serves (M3). The static PEP 503 `/simple/` tree lives under public/ and ships
// verbatim alongside the rendered catalog.
export default defineConfig({
  site: 'https://tools.culture.dev',
  output: 'static',
  integrations: [sitemap()],
});
