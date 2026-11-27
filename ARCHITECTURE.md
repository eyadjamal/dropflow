# Interface additions in 3.3

ui_theme.py centralizes native ttk typography, semantic buttons, cards, focus and selection states. output_panel.py owns the bounded form and keyboard visibility. pdf_organizer_ui.py owns the redesigned workspace and display-scaled thumbnail cards. Conversion, output routing and saved-preset model modules remain independent of these layout changes. See DESIGN.md for the visual contract.

# DropFlow 3.3 architecture

Implemented module boundaries:
- action_menu.py: action identity, categories and ranking; no Tk.
- quality_presets.py: encoder-specific quality mappings; no Tk.
- saved_presets.py: schema validation and upsert for JSON-safe named presets; no Tk.
- output_policy.py: job-local output routing with ContextVar, token validation and collision handling; no Tk.
- output_panel.py: reusable output/preset review UI with callbacks.
- pdf_organizer.py: immutable page records, reorder/rotate/delete/undo and transactional export; no Tk.
- pdf_organizer_ui.py: thumbnails, drag/reorder and selected-page preview. A single executor renders PDFs; PhotoImage and widgets are created only on the Tk thread. Documents are opened within the worker and never shared between threads.
- ui_theme.py: shared ttk palette for workflow screens and existing controls.
- batch_jobs.py: per-file records, cancellation and execution.
- DropFlow.pyw: composition, existing Tk screens and legacy conversion handlers.
- media_converter.py / office_converter.py: existing conversion engines.

Output routing is scoped to each worker action and reset in finally. It intercepts only root outputs in the source directories. Files inside newly created page/sheet/archive export folders retain their relative names. Retry uses the original settings and stable source indexes. Independent jobs retry failed inputs only. Combined jobs rerun the complete ordered selection.

Organizer export constructs a temporary PDF in the destination directory, checks cancellation, exclusively reserves the destination, and replaces only that placeholder. Failure removes temporary artifacts. Sources are not written. Document-specific page selections are not persisted in reusable presets.

Safe follow-up extraction:
1. Move batch widgets and the remaining action/quality screens into ui/.
2. Move JobContext, cancellation and password request events into jobs/context.py.
3. Move legacy PDF/archive handlers into actions/pdf.py and actions/archives.py with explicit dependencies.
4. Replace generated callback identities with explicit registry IDs as registrations migrate.
5. Move lifecycle into app.py and keep DropFlow.pyw as a thin launcher.

External Office/OCR/archive helper programs remain optional target-PC dependencies.

## Platform boundary (3.4.0)

platform_runtime.py owns configuration paths, child process groups/cancellation, opening results, Linux instance locking, desktop entries, autostart and file-manager integration. Windows native APIs and registry access remain conditional in the composition module. linux_hotkeys.py implements the hotkey interface using optional pynput on X11; Wayland uses a desktop-configured command. linux_desktop.py owns the Linux control window so missing tray support cannot make the app inaccessible. Conversion engines call the shared runtime instead of using Windows creation flags directly.

## Workspace and responsiveness (3.4.0)

- desktop_workspace.py owns the shared file chooser/drop target, recent-job table and local-history controls. Windows can hide this window while its tray remains active; Linux keeps the desktop entry point available.
- recent_activity.py validates and bounds path-only history. Incomplete large input lists cannot be reused as partial combined jobs. Missing inputs require choosing files again.
- preview_loader.py owns a bounded daemon worker and a small metadata-keyed image cache. Workers open their own documents and return PIL images through a queue. Only the Tk thread creates PhotoImage objects. Generation tokens reject stale results; window disposal closes the worker and cancels polling.
- ui_interactions.py centralizes Windows wheel and X11 Button-4/Button-5 scrolling. Action search rebuilds only list content after a short debounce and preserves the scrolling surface and focus visibility.

The persistent job queue remains future work; the workspace brings active jobs forward instead of silently cancelling or replacing them.
