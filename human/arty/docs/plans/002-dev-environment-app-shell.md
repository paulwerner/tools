# 002 — Dev Environment & App Shell (M1)

**Status:** Accepted
**Scope:** Bootstrap Arty dev environment with Docker + SvelteKit SPA and create 4-panel layout shell.

## Approach

- Multi-stage Dockerfile (Node 20 Alpine) with dev and prod targets
- docker-compose.yml with selective volume mounts and hot reload (usePolling)
- SvelteKit 2 + Svelte 5 in SPA mode (adapter-static, ssr=false)
- TypeScript strict mode
- CSS Grid 4-panel layout: toolbar, frame list, sheet preview, properties, timeline
- All panels are empty placeholders — no functional logic

## Key Decisions

- Dark theme (standard for game asset tools)
- `sirv-cli` for prod target (lightweight, SPA-aware)
- node_modules stays container-only (avoids OS/arch mismatch)
- `usePolling` for file watching in Docker

## Verification

1. `docker compose up` starts dev server without errors
2. Browser at `localhost:5173` shows 4-panel dark layout
3. Editing `.svelte` files triggers hot reload
4. `svelte-check` and `tsc --noEmit` pass with zero errors
