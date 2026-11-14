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
