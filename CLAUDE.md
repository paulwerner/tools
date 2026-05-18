# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a monorepo of independent tools, organized by intended operator:

- **`human/`** — Tools designed for direct human use (UIs, CLIs).
- **`agentic/`** — Tools designed for agentic/automated use (currently empty).

Each tool is self-contained with its own tech stack and dependencies. There is no shared build system or top-level package manager.

## Tools

### PDF Squeeze (`human/pdf_squeeze.py`)

Single-file Python 3.8+ web app for PDF compression via Ghostscript.

```bash
# Run (requires gs on PATH)
python3 human/pdf_squeeze.py
# Opens http://localhost:8484
```

**System dependency:** Ghostscript (`sudo apt install ghostscript` / `brew install ghostscript`).

No Python package dependencies — uses only stdlib. Uses `cgi.FieldStorage` for multipart parsing (deprecated in 3.11, removed in 3.13 — will need migration).

### Arty (`human/arty/`)

Browser-based game asset processing toolkit (sprite sheet assembly). Currently in design phase — only the PRD exists at `human/arty/docs/PRD.md`. No code yet.

Planned stack: SvelteKit (SPA) + TypeScript (strict) + Docker Compose for dev. All processing client-side via Canvas API and Web Workers.

## Conventions

- Tools are independent — each can have its own language, framework, and build process.
- When adding a new tool, place it under `human/` or `agentic/` depending on its intended operator, in its own subdirectory (or as a single file for simple tools).
- **Plan persistence:** When an implementation plan is accepted, persist it at `<tool-dir>/docs/plans/NNN-brief-summary.md` (zero-padded sequential number, kebab-case summary). Persisting the plan is always the first step before starting implementation. Each plan file captures scope, approach, and verification criteria.
