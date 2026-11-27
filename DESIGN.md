# DropFlow visual system (3.5)

## Palette
Midnight: background #11131c, surface #1b1e2b, border/hover #30364a, primary text #eef0f7, secondary text #a1a9be, accent #b5a0ff.
Light: background #f3f5fa, surface #ffffff, border/hover #dce3f0, primary text #182237, secondary text #59677d, accent #5944d6.
Other theme tokens and custom accents continue through appearance.py. Primary button text selects black or white for a contrast ratio of at least 4.5:1.

## Type and spacing
Segoe UI body 10 pt; secondary text and overlines 9 pt; section headings 12 pt; workflow titles 19 pt. Spacing follows 4/8/12/16/20/24 px intervals, scaled to the display. Native ttk buttons preserve keyboard focus and activation behavior.

## Components
Primary.TButton: accent-filled confirmation action.
Ghost.TButton: secondary navigation.
Action.TButton: left-aligned menu action.
Section.TButton: category disclosure with count.
Card.TFrame: bordered surface with inset content.
CardTitle/CardMuted labels: consistent surface typography.
Treeview: readable row heights and textual success/failure states with supporting color.

## Layout and interaction
The menu and output form have bounded scroll regions. The output form keeps its footer visible and reveals focused controls during keyboard navigation. Filename fields remain left-to-right; Arabic labels align to the right.
The PDF workspace separates editing, page navigation and saving. Thumbnail outlines indicate selection without obscuring the page; numbered positions and rotation badges make edits visible. Existing drag/reorder, keyboard move, delete and undo behaviors are retained.

## Checks
Contrast is covered by tests across all shipped palettes. Native Tk smoke checks cover dark/light, Arabic and 100–150% scaling. Screenshots use sample documents, not user documents.

## Workspace

A single bordered drop card leads into recent activity. Primary file selection uses the accent; folder selection, quick access, privacy and settings remain secondary. The recent table preserves selection when jobs finish. Empty and missing-file states explain the next action. Background preview slots keep a fixed size to avoid layout jumps.

Search supports Ctrl+F, Down/Up, Enter and Escape-to-clear. Native Tab focus remains available. Dark/light surfaces share the same geometry; fonts fall back to Noto Sans or DejaVu Sans on Linux. Recent activity can be disabled or cleared without deleting files.
