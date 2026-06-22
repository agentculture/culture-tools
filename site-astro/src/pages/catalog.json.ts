// /catalog.json — the machine-readable catalog the site renders from, exposed as
// a stable endpoint for agents and tooling.
import type { APIRoute } from 'astro';
import { catalog } from '../data/catalog.ts';

export const GET: APIRoute = () =>
  new Response(JSON.stringify(catalog, null, 2) + '\n', {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
