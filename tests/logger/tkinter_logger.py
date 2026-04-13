import argparse
import tkinter as tk
from hyper_framework.message_logger import (
    SingletonSystemLogger,
    DarkThemeTkinterAdapter,
    LightThemeTkinterAdapter,
)


def create_app(initial_theme: str = "dark"):
    root = tk.Tk()
    root.title("Logger Theme Switch")

    text = tk.Text(root)
    text.pack(fill="both", expand=True)

    logger = SingletonSystemLogger()

    def set_theme(theme: str):
        logger.clear_adapters()
        if theme == "dark":
            text.configure(bg="#1e1e1e", fg="#ffffff")
            logger.register_adapter(DarkThemeTkinterAdapter("INFO", tk_window=text))
        else:
            text.configure(bg="#ffffff", fg="#000000")
            logger.register_adapter(LightThemeTkinterAdapter("INFO", tk_window=text))

    def toggle_theme():
        root.current_theme = "light" if root.current_theme == "dark" else "dark"
        set_theme(root.current_theme)

    btn = tk.Button(root, text="Toggle Theme", command=toggle_theme)
    btn.pack(anchor="ne", padx=8, pady=8)

    root.current_theme = initial_theme
    set_theme(root.current_theme)

    # Example logs to show in the text widget
    logger.info("INFO 訊息")
    logger.warning("WARNING 訊息")
    logger.shiny_log("閃亮節點", "CHECKPOINT")

    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tkinter logger theme switcher")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark", help="initial theme")
    args = parser.parse_args()

    app = create_app(initial_theme=args.theme)
    app.mainloop()