"""Compatibility entry point for the shared desktop workspace."""
def build_control_window(app, translate=lambda s: s):
    return app.open_workspace()
