import tkinter as tk

class IScalableWindowTester:
    """
        A mixin class for tkinter windows that logs the current width and height
        on every resize event. This is particularly useful for developers to observe
        the actual rendered size of the window after layout, helping to determine
        appropriate values for `minsize`, `geometry`, or other size constraints.

        This class should be used in combination with a tkinter window class,
        such as `tk.Toplevel` or `tk.Tk`.

        Example:
            class MyWindow(tk.Toplevel, IScalableWindowTester):
                def __init__(self, master):
                    tk.Toplevel.__init__(self, master)
                    IScalableWindowTester.__init__(self)
                    # self.minsize(width=600, height=400)
                    # Run once, observe output, then set final minsize accordingly

        Output Example:
            [Resize] Width=684, Height=647

        Note:
            This class only logs the size and does not modify the window itself.
            Once the desired window size is confirmed, the mixin can be removed from the class.
    """

    def __init__(self, *args, **kwargs):
        # 假設子類會呼叫 super().__init__(*args, **kwargs)
        # 綁定尺寸變化事件
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        # event.width / event.height 是視窗目前大小
        print(f"[Resize] height={event.height}, width={event.width}")


class WidgetResizeLogger:
    """
        A utility class to help developers debug widget layout in tkinter.

        This class allows you to bind a resize event listener to any tkinter widget
        (e.g., Frame, Canvas, Label, etc.), so you can monitor its width and height
        whenever it changes. It's particularly useful when debugging layout issues,
        such as widgets not appearing, being squashed, or getting hidden.

        Usage:
            WidgetResizeLogger.bind_resize_logger(widget, tag="[MyWidget]")
            # self.module_info_holder_frame.config(width=670, height=50)
            # self.module_info_holder_frame.pack_propagate(False)  # 如果要固定尺寸不被內容自動撐開
            # Run once, observe output, then set final minsize accordingly

        Example:
            frame = tk.Frame(parent)
            WidgetResizeLogger.bind_resize_logger(frame, tag="[InfoFrame]")

        Output Example:
            [InfoFrame] Width=670, Height=200

        Note:
            This logger only prints size changes to the console.
            It does not interfere with the layout or widget behavior.
    """
    @staticmethod
    def bind_resize_logger(widget: tk.Widget, tag="[Resize]"):
        """Bind a configure event to print the widget's size whenever it changes."""
        def _log(event):
            print(f"{tag} Width={event.width}, Height={event.height}")
        widget.bind("<Configure>", _log)


