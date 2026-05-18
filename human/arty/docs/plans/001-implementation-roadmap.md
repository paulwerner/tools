# 001 — Implementation Roadmap

**Status:** Accepted
**Scope:** Break the Arty PRD into 19 concrete, self-contained milestones across 3 phases, producing `docs/roadmap.md`.

## Approach

Each milestone is designed to be implementable in a single focused session, leaving the app in a working, demoable state. Milestones specify scope, key files, dependencies on prior milestones, and verification criteria.

### Phase 1 — MVP (Sprite Sheet Assembly): 11 milestones (M1–M11)

Covers PRD features 3.1–3.7 plus polish. Key ordering decisions:
- M3 (reorder) and M4 (grid/preview) are parallelizable — both depend on M2 but not each other.
- Persistence (M5) comes after M4 so there's meaningful state to persist.
- Duplicate detection (M8) and cleanup (M9) are split — detection is read-only and independently useful.

### Phase 2 — Image Operations: 4 milestones (M12–M15)

Operation stack infrastructure (M12) first, then three independent operations (scale, palette, background removal).

### Phase 3 — Advanced: 4 milestones (M16–M19)

Sprite sheet slicing, batch processing, trim & pack, operation presets — all depend on M12.

## Verification

- Every PRD feature (3.1–3.14) maps to exactly one milestone
- No circular dependencies in the milestone graph
- Each milestone has concrete verification criteria
