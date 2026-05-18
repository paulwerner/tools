# Session 001 — Dev Environment & App Shell (M1)

**Date:** 2026-05-18
**Milestone:** M1
**Plan:** `docs/plans/002-dev-environment-app-shell.md`

## Summary

Bootstrapped the Arty project from zero code to a working containerized SvelteKit SPA with a 4-panel layout shell.

## What was built

- **Docker setup:** Multi-stage Dockerfile (Node 20 Alpine) with dev and prod targets. `docker-compose.yml` with selective volume mounts (`src/`, `static/`, config files) — `node_modules` stays container-only.
- **SvelteKit SPA:** Svelte 5 + TypeScript strict + Vite 6 + `adapter-static` with `fallback: 'index.html'` for SPA mode. SSR disabled globally via `+layout.ts`.
- **App shell:** 4-panel CSS Grid layout (toolbar, frame list, sheet preview, properties panel, animation timeline) with dark theme. All panels are placeholders with labels; toolbar buttons are disabled.
- **Hot reload:** Vite file watching uses `usePolling` for Docker bind mount compatibility.

## Files created (18)

```
human/arty/
├── .dockerignore
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── package.json
├── package-lock.json
├── svelte.config.js
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── app.html
    ├── app.css
    ├── app.d.ts
    ├── routes/
    │   ├── +layout.svelte
    │   ├── +layout.ts
    │   └── +page.svelte
    └── components/
        └── AppShell.svelte
```

## Issues encountered and resolved

1. **`forceConsistentCasingInImports` vs `forceConsistentCasingInFileNames`:** The initial tsconfig used the wrong TypeScript compiler option name. `svelte-check` caught it. Fixed to `forceConsistentCasingInFileNames`. See learning 001.
2. **`@types/node` missing:** SvelteKit's generated tsconfig references `"types": ["node"]`, which requires `@types/node` as a devDependency. Added it to `package.json`.
3. **`npm ci` timeout in Docker:** First build hit an npm exit handler bug on Node 20 Alpine. Resolved by using `npm ci || npm install` fallback in the Dockerfile. Subsequent builds used `npm ci` successfully.

## Verification

All four M1 criteria passed:
1. `docker compose up` — dev server starts without errors
2. `localhost:5173` — returns HTTP 200 (SPA renders client-side)
3. `svelte-check` — 0 errors, 0 warnings
4. `tsc --noEmit` — 0 errors

## Convention changes

Added three new conventions to `CLAUDE.md`:
- **Commit after verification** — commit locally once changes pass all checks
- **Session summaries** — create only after explicit user approval
- **Learnings** — record non-obvious issues with session references
