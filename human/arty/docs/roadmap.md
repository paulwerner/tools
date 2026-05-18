# Arty — Implementation Roadmap

This roadmap breaks the [PRD](PRD.md) into self-contained milestones. Each milestone is independently implementable, leaves the app in a working state, and has concrete verification criteria.

PRD section references use the format `§3.N`.

---

## Dependency Graph

```
M1  Dev Environment & App Shell
 │
M2  Image Import & Frame List
 ├────────────┐
M3  Reorder   M4  Grid & Preview
 │            ├────────────┬──────────┐
 │            M5  Persist  M8  Dup.Det│
 │            │            │          │
 └─────┬──────┘            │          │
      M6  Anim. Tagging    │          │
       │   ┌───────────────┘          │
       │  M9  Dup. Cleanup            │
       ├───┘                          │
      M7  Anim. Preview               │
       │                              │
      M10  Export ────────────────────┘
       │
      M11  Polish & UX
       │
      M12  Op Stack Infrastructure
       ├──────────┬──────────┐
      M13 Scale  M14 Palette M15 BG Remove
       │          │           │
      M16 Slice  M17 Batch  M18 Trim&Pack  M19 Presets
```

---

## Phase 1 — MVP (Sprite Sheet Assembly)

### M1: Dev Environment & App Shell

**PRD refs:** §4.1, §4.4, §1.1 (containerized development)

**Scope:**

- Multi-stage Dockerfile (Node 20 LTS — dev + prod targets)
- `docker-compose.yml` with hot reload and volume mounts
- SvelteKit project scaffolded in SPA mode (`adapter-static`)
- TypeScript strict mode enabled
- Vite config
- Base layout shell: 4-panel structure (frame list, sheet preview, properties panel, animation timeline) — empty placeholders

**Key files:**

```
arty/
├── Dockerfile
├── docker-compose.yml
├── svelte.config.js
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── app.html
│   ├── routes/+page.svelte
│   └── components/AppShell.svelte
```

**Depends on:** —

**Verification:**

1. `docker compose up` starts the dev server without errors
2. Browser at `localhost:5173` (or configured port) shows the 4-panel layout shell
3. Editing a `.svelte` file triggers hot reload
4. `npx svelte-check` and `npx tsc --noEmit` pass with zero errors

---

### M2: Image Import & Frame List

**PRD refs:** §3.1

**Scope:**

- `ImportPanel` component: drag-and-drop zone + file picker for PNG files
- Read files as Blobs, generate thumbnails via Canvas API
- `FrameList` component: vertical thumbnail strip showing filename, dimensions, and file size
- Core data model types: `SourceFrame`, `ArtyProject` (initial shape)
- Project store (Svelte writable store) holding frame state
- Warn on dimension mismatches (e.g., mixed 32×32 and 64×64) — non-blocking banner

**Key files:**

```
src/
├── lib/
│   ├── core/types.ts
│   └── stores/project.ts
├── components/
│   ├── ImportPanel.svelte
│   └── FrameList.svelte
```

**Depends on:** M1

**Verification:**

1. Drop multiple PNGs onto the drop zone — they appear as thumbnails
2. Each thumbnail shows filename, pixel dimensions, and file size
3. Dropping a mix of 32×32 and 64×64 frames shows a dimension mismatch warning
4. Non-PNG files are ignored

---

### M3: Frame Reordering

**PRD refs:** §3.2 (drag-and-drop reordering)

**Scope:**

- Drag-and-drop reordering in `FrameList`
- `DragHandle` common component
- `frameOrder` array in project store, updated on reorder
- Visual feedback during drag (ghost element, drop indicator)

**Key files:**

```
src/
├── components/
│   ├── FrameList.svelte  (updated)
│   └── common/DragHandle.svelte
├── lib/stores/project.ts  (frameOrder)
```

**Depends on:** M2

**Verification:**

1. Drag a frame from position 1 to position 4 — frame list updates, order persists
2. Drag indicator shows valid drop targets
3. Reordering 10+ frames remains responsive

---

### M4: Grid Assembly & Sheet Preview

**PRD refs:** §3.2 (grid layout, padding, live preview)

**Scope:**

- `GridConfig` data model and controls
- `GridConfigurator` component: columns, rows (or auto), border/cell/inner padding sliders
- `assembler.ts`: layout algorithm + canvas-based sheet composition
- `SheetPreview` component: renders assembled sheet on a `<canvas>`, zoomable (scroll wheel) and pannable (click-drag)
- Live preview updates when grid config or frame order changes

**Key files:**

```
src/
├── lib/core/
│   ├── types.ts  (GridConfig)
│   └── assembler.ts
├── components/
│   ├── GridConfigurator.svelte
│   └── SheetPreview.svelte
├── lib/stores/project.ts  (grid config)
```

**Depends on:** M2

**Verification:**

1. Import 12 frames, set columns=4 — preview shows 4×3 grid
2. Adjust cell padding to 2px — preview updates in real time with visible spacing
3. Zoom in/out with scroll wheel, pan with click-drag
4. Change column count — row count auto-adjusts, preview re-renders

---

### M5: Persistence

**PRD refs:** §4.1 (IndexedDB via idb), §10 (project persistence decisions)

**Scope:**

- IndexedDB schema via `idb` wrapper: projects table, frames blob store
- `db.ts`: schema definition, migrations
- `project-store.ts`: auto-save on state change (debounced 500ms), load on startup
- `serialization.ts`: `ArtyProject` ↔ JSON for `.arty.json` export/import
- `ProjectList` component: list, switch, delete projects
- Manual export/import of `.arty.json` files

**Key files:**

```
src/lib/persistence/
├── db.ts
├── project-store.ts
└── serialization.ts
src/components/ProjectList.svelte
```

**Depends on:** M4 (needs meaningful project state — frames + grid config)

**Verification:**

1. Import frames, configure grid → close browser tab → reopen → project restored exactly
2. Create two projects, switch between them — each retains its own state
3. Export `.arty.json`, delete project, import `.arty.json` — project restored
4. Delete a project — it disappears from the list, its IndexedDB data is cleaned up

---

### M6: Animation Tagging

**PRD refs:** §3.3

**Scope:**

- `AnimationTag` data model (name, from, to, direction, fps)
- `TagEditor` component: create/edit/delete tags
- Frame range selection in `FrameList` (shift-click or drag-select)
- Default fps: 10, overridable per tag
- Direction options: forward, reverse, ping-pong
- Visual tag indicators on frame list (colored range underlines)

**Key files:**

```
src/
├── lib/core/types.ts  (AnimationTag)
├── lib/stores/project.ts  (tags array)
├── components/TagEditor.svelte
├── components/FrameList.svelte  (selection, tag indicators)
```

**Depends on:** M3 (frame ordering), M4 (frames in grid context)

**Verification:**

1. Select frames 0–3, create tag "idle" at 10 FPS forward — appears in TagEditor
2. Select frames 4–11, create tag "run" at 12 FPS — second tag listed
3. Edit "idle" to ping-pong direction — tag updates
4. Delete "run" — removed from list, frame indicators clear
5. Reorder frames — tag indices adjust if needed

---

### M7: Animation Preview & Playback

**PRD refs:** §3.4

**Scope:**

- `AnimationPlayer` component in the bottom timeline panel
- Playback engine: `requestAnimationFrame`-based, respects tag fps
- Controls: play/pause, frame-by-frame step (forward/back), speed multiplier (0.25×–4×)
- Tag selector: play a specific tag or all frames
- Onion skinning toggle: overlay previous/next N frames at reduced opacity
- Current frame indicator: highlighted in frame list and sheet preview

**Key files:**

```
src/components/
├── AnimationPlayer.svelte
├── FrameList.svelte  (current frame highlight)
├── SheetPreview.svelte  (current frame highlight, onion skin overlay)
```

**Depends on:** M6

**Verification:**

1. Select "idle" tag → press play → frames 0–3 animate at 10 FPS
2. Adjust speed to 0.5× → animation slows accordingly
3. Step forward/back → frame advances/retreats one at a time
4. Enable onion skinning → previous frame visible at reduced opacity
5. Current frame highlighted in both frame list and sheet preview during playback

---

### M8: Duplicate Detection

**PRD refs:** §3.5 (visual grouping, configuration)

**Scope:**

- `hasher.ts`: perceptual hashing algorithm (dHash or pHash)
- `hash.worker.ts`: Web Worker for off-thread hash computation
- Color-coded duplicate group borders in frame list and sheet preview
- Each group gets a distinct high-contrast color
- Hover a duplicate → all group members highlight (pulse/brighten)
- Duplicate summary badge: "N groups, M removable frames"
- Configuration: exact pixel match vs perceptual (with tolerance slider), alpha channel include/exclude toggle

**Key files:**

```
src/
├── lib/core/hasher.ts
├── lib/workers/hash.worker.ts
├── components/FrameList.svelte  (group borders, hover)
├── components/SheetPreview.svelte  (group borders)
```

**Depends on:** M4 (sheet preview for visual borders)

**Verification:**

1. Import a set containing 2 identical frames and 1 unique frame — identical pair gets a colored border, unique frame has none
2. Hover one duplicate → the other highlights
3. Summary badge shows "1 group, 1 removable frame"
4. Switch from exact to perceptual mode with a near-duplicate pair → detection picks it up

---

### M9: Duplicate Cleanup

**PRD refs:** §3.5 (cleanup workflow)

**Scope:**

- Click duplicate group badge → frame list filters/scrolls to show group members
- Select which frames to keep vs remove
- "Auto-remove all duplicates" action (keeps first occurrence per group), with confirmation dialog
- Removing a frame: grid layout re-renders, tag indices auto-adjust (shift `from`/`to` for affected tags, remove tags that become empty)

**Key files:**

```
src/components/
├── FrameList.svelte  (filter, select, remove)
├── TagEditor.svelte  (index adjustment on frame removal)
├── SheetPreview.svelte  (re-render on removal)
```

**Depends on:** M8 (detection), M6 (tag index adjustment)

**Verification:**

1. With 2 duplicate frames (indices 0 and 4): remove frame 4 → grid shrinks by one cell, tag starting at 4 shifts to 3
2. Auto-remove all duplicates → confirmation dialog → duplicates removed, first occurrences kept
3. A tag spanning removed frames adjusts correctly; a tag that becomes empty is deleted

---

### M10: Export

**PRD refs:** §3.6, §3.7

**Scope:**

- `metadata.ts`: builds Aseprite-compatible JSON (frames array format, frameTags, duplicates extension)
- `exporter.ts`: renders final sheet from canvas to PNG Blob, generates JSON, packages as ZIP (multi-file) or direct download (single file)
- `ExportPanel` component: filename input, quality settings, download button
- Duration computation: `Math.round(1000 / fps)` per tag

**Key files:**

```
src/
├── lib/core/
│   ├── metadata.ts
│   └── exporter.ts
├── components/ExportPanel.svelte
```

**Depends on:** M6 (tags for frameTags in JSON), M4 (assembled sheet for PNG)

**Verification:**

1. Full workflow: import frames → arrange → tag → export → download ZIP containing PNG + JSON
2. JSON validates against the Aseprite json-array schema structure from PRD §3.6
3. Frame dimensions and positions in JSON match the actual PNG sheet
4. `duration` values match `Math.round(1000 / fps)` for each tag's frames
5. Single-file export produces a direct PNG download (no ZIP)

---

### M11: Polish & UX

**PRD refs:** §3.2 (edge pixel extrusion), §7 (undo/redo, constraints)

**Scope:**

- Keyboard shortcuts (import, undo/redo, playback, zoom)
- Undo/redo: command pattern over `ArtyProject` state — each user action pushes an undoable command
- Responsive layout: properties panel collapses on narrow viewports
- Edge pixel extrusion option in `GridConfigurator` (N pixels, prevents texture bleeding)
- Sheet size warning when exceeding 4096×4096 (configurable limit per §7)
- File size warnings (>10MB individual, >100MB total)

**Key files:**

```
src/
├── lib/core/assembler.ts  (extrusion)
├── lib/stores/project.ts  (undo/redo stack)
├── components/GridConfigurator.svelte  (extrusion control, size warning)
├── components/AppShell.svelte  (responsive breakpoints, keyboard handler)
```

**Depends on:** M1–M10 (final integration pass)

**Verification:**

1. Ctrl+Z undoes the last action, Ctrl+Shift+Z redoes it — works for reorder, tag changes, grid config changes
2. Set edge extrusion to 1px → sheet preview shows extruded pixels at frame edges
3. Resize browser window to narrow width → properties panel collapses
4. Assemble a sheet exceeding 4096×4096 → warning appears
5. Keyboard shortcuts for play/pause, step, zoom in/out all function

---

## Phase 2 — Image Operations

### M12: Operation Stack Infrastructure

**PRD refs:** §4.3 (processing pipeline), §4.5 (extension points)

**Scope:**

- `Operation` data model, `OperationType` union, operation registry
- `pipeline.ts`: sequential stack executor — each operation receives an `ImageBitmap`, returns a new one
- `process.worker.ts`: Web Worker for off-thread pipeline execution
- Pipeline caching: skip re-execution when operation params haven't changed
- `OperationStack` component: add/remove operations, toggle enabled, drag-to-reorder, per-operation parameter UI
- Preview integration: sheet preview shows result after all enabled operations

**Key files:**

```
src/
├── lib/core/
│   ├── types.ts  (Operation, OperationType)
│   ├── pipeline.ts
│   └── operations/types.ts
├── lib/workers/process.worker.ts
├── components/OperationStack.svelte
```

**Depends on:** M11

**Verification:**

1. Add a no-op operation → pipeline runs, preview unchanged
2. Toggle an operation off → preview updates without that operation
3. Reorder operations → preview reflects new order
4. Pipeline caching: change an unrelated control → operations don't re-execute (verify via console timing or worker messages)

---

### M13: Scale Operation

**PRD refs:** §3.8

**Scope:**

- `scale.ts`: integer scale factors (1×–4×), interpolation modes (nearest-neighbor, bilinear, bicubic)
- Downscale with non-integer factor on pixel art → warning
- Integrated into operation stack and preview

**Key files:**

```
src/lib/core/operations/scale.ts
```

**Depends on:** M12

**Verification:**

1. Add scale 2× with nearest-neighbor → preview shows pixel-perfect 2× upscale
2. Switch to bilinear → visible smoothing difference
3. Scale down 0.5× on pixel art → warning displayed
4. Toggle scale off → preview reverts to original size

---

### M14: Palette Operations

**PRD refs:** §3.9

**Scope:**

- `palette.ts`: reduce to N colors (median-cut or k-means), map to imported palette, extract palette
- `palette-io.ts`: parse and write `.gpl`, `.pal`, `.hex`, `.ase`, JSON palette formats
- `palette-presets.ts`: built-in palettes (PICO-8, NES, Game Boy, etc.)
- Dithering: none, Floyd-Steinberg, ordered (Bayer matrix), with strength control

**Key files:**

```
src/lib/
├── core/operations/palette.ts
├── utils/
│   ├── palette-io.ts
│   └── palette-presets.ts
```

**Depends on:** M12

**Verification:**

1. Reduce to 4 colors → preview shows quantized result
2. Map to PICO-8 palette → colors remapped to the 16-color PICO-8 set
3. Import a `.gpl` file → palette loaded, mapping applied
4. Enable Floyd-Steinberg dithering → visible dither pattern
5. Extract palette from current frames → palette displayed, exportable as `.hex`

---

### M15: Background Removal

**PRD refs:** §3.10

**Scope:**

- `background.ts`: color-key removal (click pixel or enter hex), tolerance control
- Contiguous mode: flood-fill based — only removes connected regions of the key color
- Edge refinement: 1px anti-alias cleanup at transparency boundaries

**Key files:**

```
src/lib/core/operations/background.ts
```

**Depends on:** M12

**Verification:**

1. Click a background pixel → all matching pixels become transparent in preview
2. Set tolerance to 10 → near-matching colors also removed
3. Enable contiguous mode → only the clicked region removed, interior same-color pixels preserved
4. Enable edge refinement → boundary pixels smoothed

---

## Phase 3 — Advanced Features

### M16: Sprite Sheet Slicing

**PRD refs:** §3.11

**Scope:**

- Import an existing sprite sheet image
- Define grid: cell width × height input, or auto-detect from visual gaps/spacing
- Slice into individual `SourceFrame` entries fed into the standard pipeline

**Depends on:** M12

**Verification:**

1. Import a 256×128 sprite sheet, set cell size 32×32 → 32 frames extracted
2. Auto-detect on a sheet with 1px gaps → correct grid detected
3. Sliced frames appear in the frame list, usable in all downstream features

---

### M17: Batch Processing

**PRD refs:** §3.12

**Scope:**

- Define a reusable operation pipeline
- Apply to a set of input files
- Output naming: `{original_name}_processed.png`

**Depends on:** M12

**Verification:**

1. Configure pipeline (scale 2× → reduce to 16 colors) → select 5 input PNGs → download 5 processed PNGs
2. Output filenames follow `{name}_processed.png` convention
3. Processing runs in Web Worker — UI remains responsive

---

### M18: Trim & Pack

**PRD refs:** §3.13

**Scope:**

- Trim transparent borders from each frame, track offset in `spriteSourceSize`
- Bin-packing layout as alternative to grid — minimize atlas waste for irregular-size frames
- JSON export: `trimmed: true`, populated `spriteSourceSize`

**Depends on:** M12

**Verification:**

1. Frames with large transparent borders → trimmed, sheet visibly smaller
2. JSON export shows `trimmed: true` and correct `spriteSourceSize` offsets
3. Bin-pack mode with mixed-size frames → tighter packing than grid layout
4. Game engine loads the trimmed sheet + JSON correctly (sprite positions match)

---

### M19: Operation Presets

**PRD refs:** §3.14

**Scope:**

- Save current operation stack as a named preset
- Load presets from a list
- Stored in IndexedDB alongside projects
- Export/import presets as JSON

**Depends on:** M12

**Verification:**

1. Configure operations → save as "pixel-art-export" → preset appears in list
2. New project → load preset → operations applied identically
3. Export preset as JSON → import in another browser session → preset restored

