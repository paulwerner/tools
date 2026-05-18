<div class="app-shell">
	<header class="toolbar">
		<span class="toolbar-brand">Arty</span>
		<div class="toolbar-actions">
			<button disabled>Import</button>
			<button disabled>Export</button>
			<button disabled>Undo</button>
			<button disabled>Redo</button>
			<button disabled>Settings</button>
		</div>
	</header>

	<aside class="frame-list">
		<div class="panel-header">Frames</div>
		<div class="panel-placeholder">Frame list will appear here</div>
	</aside>

	<main class="sheet-preview">
		<div class="panel-header">Sheet Preview</div>
		<div class="panel-placeholder">Canvas preview will appear here</div>
	</main>

	<aside class="properties">
		<div class="panel-header">Properties</div>
		<div class="panel-placeholder">Grid config, operations, and tag editor will appear here</div>
	</aside>

	<footer class="timeline">
		<div class="panel-header">Animation Timeline</div>
		<div class="panel-placeholder">Playback controls and timeline will appear here</div>
	</footer>
</div>

<style>
	.app-shell {
		display: grid;
		grid-template-columns: var(--frame-list-width) 1fr var(--properties-width);
		grid-template-rows: var(--toolbar-height) 1fr var(--timeline-height);
		grid-template-areas:
			'toolbar toolbar toolbar'
			'frames preview properties'
			'timeline timeline timeline';
		height: 100vh;
		width: 100vw;
		gap: 1px;
		background-color: var(--color-border);
	}

	.toolbar {
		grid-area: toolbar;
		background-color: var(--color-surface);
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 16px;
	}

	.toolbar-brand {
		font-weight: 700;
		font-size: 18px;
		color: var(--color-accent);
	}

	.toolbar-actions {
		display: flex;
		gap: 8px;
	}

	.toolbar-actions button {
		background: var(--color-bg);
		color: var(--color-text-muted);
		border: 1px solid var(--color-border);
		border-radius: 4px;
		padding: 6px 12px;
		cursor: not-allowed;
		font-size: 13px;
	}

	.frame-list {
		grid-area: frames;
		background-color: var(--color-surface);
		overflow-y: auto;
	}

	.sheet-preview {
		grid-area: preview;
		background-color: var(--color-bg);
		overflow: hidden;
	}

	.properties {
		grid-area: properties;
		background-color: var(--color-surface);
		overflow-y: auto;
	}

	.timeline {
		grid-area: timeline;
		background-color: var(--color-surface);
		overflow-x: auto;
	}

	.panel-header {
		padding: 8px 12px;
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-muted);
		border-bottom: 1px solid var(--color-border);
	}

	.panel-placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		height: calc(100% - 35px);
		color: var(--color-text-muted);
		font-size: 13px;
		font-style: italic;
	}
</style>
