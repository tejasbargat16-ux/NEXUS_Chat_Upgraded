"""
Desktop native UI and system tray integration for NEXUS v2.
Embeds the NEXUS Studio web HUD using pywebview, adds a persistent
system tray icon using pystray, and handles window minimization to tray.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable

logger = logging.getLogger("nexus.desktop.ui")


def create_tray_icon_image():
    """Generate a clean 64x64 icon for the system tray using Pillow."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Draw a glowing cyan/violet circle with an 'N' mark
        draw.ellipse([4, 4, 60, 60], fill=(6, 182, 212, 255), outline=(139, 92, 246, 255), width=3)
        draw.polygon([(22, 48), (22, 16), (42, 48), (42, 16)], fill=(255, 255, 255, 255))
        return img
    except Exception as exc:
        logger.warning("Failed to create custom tray icon image: %s", exc)
        from PIL import Image
        return Image.new("RGB", (64, 64), color=(6, 182, 212))


class DesktopUI:
    """Manages the pywebview native desktop window and pystray tray icon."""

    def __init__(self, target_url: str = "http://127.0.0.1:5000"):
        self.target_url = target_url
        self.window = None
        self.tray_icon = None
        self._is_running = False

    def setup_tray(self) -> None:
        """Initialize the background system tray icon."""
        try:
            import pystray

            def on_show(icon, item):
                if self.window:
                    try:
                        self.window.show()
                        self.window.restore()
                    except Exception:
                        pass

            def on_hide(icon, item):
                if self.window:
                    try:
                        self.window.hide()
                    except Exception:
                        pass

            def on_quit(icon, item):
                self._is_running = False
                icon.stop()
                if self.window:
                    try:
                        self.window.destroy()
                    except Exception:
                        pass

            menu = pystray.Menu(
                pystray.MenuItem("Show NEXUS", on_show, default=True),
                pystray.MenuItem("Hide NEXUS", on_hide),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", on_quit),
            )

            icon_img = create_tray_icon_image()
            self.tray_icon = pystray.Icon("NEXUS_v2", icon_img, "NEXUS v2 Desktop Assistant", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            logger.info("System tray icon initialized.")
        except Exception as exc:
            logger.warning("System tray initialization failed: %s", exc)

    def launch(
        self,
        title: str = "NEXUS v2 — Desktop AI Assistant",
        width: int = 1280,
        height: int = 840,
    ) -> None:
        """Start the native desktop window via pywebview."""
        import webview

        self._is_running = True
        self.setup_tray()

        self.window = webview.create_window(
            title=title,
            url=self.target_url,
            width=width,
            height=height,
            resizable=True,
            min_size=(900, 600),
            background_color="#04060c",
        )

        webview.start(debug=False)


def launch_ui(url: str = "http://127.0.0.1:5000") -> None:
    """Convenience launcher for the desktop UI."""
    ui = DesktopUI(target_url=url)
    ui.launch()
