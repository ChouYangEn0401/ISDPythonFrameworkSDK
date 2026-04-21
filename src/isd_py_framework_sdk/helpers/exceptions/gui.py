"""
GUI exceptions — errors that occur in graphical user-interface operations,
widget management, layout rendering, and event handling.
"""


class WidgetNotFoundError(Exception):
    """Raised when a widget lookup by name, ID, or path returns no result."""

    def __init__(self, widget_id: str = "", message: str | None = None):
        if message is None:
            if widget_id:
                message = f"Widget '{widget_id}' could not be found."
            else:
                message = "The requested widget could not be found."
        super().__init__(message)
        self.widget_id = widget_id


class UIStateError(Exception):
    """Raised when a UI operation is attempted while the interface is in an incompatible state."""

    def __init__(self, current_state: str = "", message: str | None = None):
        if message is None:
            if current_state:
                message = f"UI operation cannot be performed in the current state: '{current_state}'."
            else:
                message = "UI operation cannot be performed in the current state."
        super().__init__(message)
        self.current_state = current_state


class RenderError(Exception):
    """Raised when a rendering/drawing operation fails (canvas, image, template, …)."""

    def __init__(self, component: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Failed to render '{component}'"] if component else ["Render failed"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.component = component
        self.reason = reason


class EventHandlerError(Exception):
    """Raised when a GUI event handler raises an unhandled exception."""

    def __init__(self, event: str = "", handler: str = "", reason: str = "", message: str | None = None):
        if message is None:
            if event and handler:
                msg = f"Event handler '{handler}' for event '{event}' raised an error"
            elif event:
                msg = f"Event handler for '{event}' raised an error"
            else:
                msg = "A GUI event handler raised an error"
            message = (msg + f": {reason}.") if reason else (msg + ".")
        super().__init__(message)
        self.event = event
        self.handler = handler
        self.reason = reason


class LayoutError(Exception):
    """Raised when a layout calculation or geometry management fails."""

    def __init__(self, detail: str = "", message: str | None = None):
        if message is None:
            message = f"Layout error: {detail}." if detail else "A layout error occurred."
        super().__init__(message)
        self.detail = detail


class ThemeNotFoundError(Exception):
    """Raised when a requested UI theme or style definition cannot be found."""

    def __init__(self, theme: str = "", message: str | None = None):
        if message is None:
            if theme:
                message = f"Theme '{theme}' could not be found."
            else:
                message = "The requested theme could not be found."
        super().__init__(message)
        self.theme = theme


class WindowNotOpenError(Exception):
    """Raised when an operation requires an open window but the window is closed or not yet created."""

    def __init__(self, window: str = "", message: str | None = None):
        if message is None:
            if window:
                message = f"Window '{window}' is not open."
            else:
                message = "The target window is not open."
        super().__init__(message)
        self.window = window


class ScreenResolutionError(Exception):
    """Raised when the screen or window resolution is incompatible with the UI layout."""

    def __init__(self, required: str = "", actual: str = "", message: str | None = None):
        if message is None:
            if required and actual:
                message = f"Screen resolution {actual} is incompatible with required resolution {required}."
            else:
                message = "Screen resolution is incompatible with the UI layout."
        super().__init__(message)
        self.required = required
        self.actual = actual
