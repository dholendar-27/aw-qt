import sys
import logging
import subprocess
import time
import webbrowser
from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMessageBox,
    QMenu,
    QWidget,
)
from PySide6.QtGui import QIcon, QAction
from PySide6 import QtCore
from pathlib import Path
import os
from .util import retrieve_settings, add_settings
from .manager import Manager

logger = logging.getLogger(__name__)

manager = Manager()

# Function to open URLs
def open_url(url: str) -> None:
    if sys.platform == "linux":
        subprocess.Popen(["xdg-open", url])
    else:
        webbrowser.open(url)

def open_webui(root_url: str) -> None:
    """Open the web dashboard."""
    open_url(root_url)

def open_dir(d: str) -> None:
    """Open a directory in the system's default file manager."""
    if sys.platform == "win32":
        os.startfile(d)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", d])
    else:
        subprocess.Popen(["xdg-open", d])

class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, parent: QWidget = None):
        super().__init__(icon, parent)
        self._parent = parent
        self.root_url = "http://localhost:7600"
        self.activated.connect(self.on_activated)

        self.settings = None  # Initially, settings will be None
        self._build_rootmenu()  # Build the tray menu initially (empty or with default options)

    def _build_rootmenu(self):
        """Build the context menu based on the settings."""
        menu = QMenu(self._parent)

        # Fetch settings dynamically every time the tray menu is opened
        self.settings = retrieve_settings()  # Retrieve settings from the server

        if self.settings:
            # Settings are available, show options like Dashboard, Launch on Start, Idle Time, and Schedule
            menu.addAction("Open Dashboard", lambda: open_webui(self.root_url))

            # Launch on Start (with a checkbox)
            self.launch_action = QAction("Launch on Start", self)
            self.launch_action.setCheckable(True)
            self.launch_action.setChecked(self.settings.get("launch", False))
            self.launch_action.triggered.connect(self.toggle_launch_on_start)
            menu.addAction(self.launch_action)

            # Enable Idle Time (with a checkbox)
            self.idle_time_action = QAction("Enable Idle Time", self)
            self.idle_time_action.setCheckable(True)
            self.idle_time_action.setChecked(self.settings.get("idle_time", False))
            self.idle_time_action.triggered.connect(self.toggle_idle_time)
            menu.addAction(self.idle_time_action)

            # Schedule sub-menu with days of the week
            weekdays = self.settings.get('weekdays_schedule', {})
            schedule_menu = menu.addMenu("Schedule")
            for day, enabled in weekdays.items():
                if day not in ["endtime", "starttime"]:  # Skip endtime/starttime
                    day_action = QAction(f"{day}", self)
                    day_action.setCheckable(True)
                    day_action.setChecked(enabled)
                    day_action.triggered.connect(lambda _, d=day: self.toggle_day_schedule(d))
                    schedule_menu.addAction(day_action)

            menu.addSeparator()

        else:
            # If settings are not available (first time user or no settings), show the login option
            menu.addAction("Login",  lambda: open_webui(self.root_url))

        # Quit option always available
        menu.addAction("Quit", quit_application)

        self.setContextMenu(menu)

    def toggle_launch_on_start(self):
        """Toggle the 'Launch on Start' setting."""
        launch_on_start = not self.settings.get("launch", False)
        add_settings("launch", launch_on_start)
        self.launch_action.setChecked(launch_on_start)  # Update the checkbox state
        logger.info(f"Launch on start set to {launch_on_start}")

    def toggle_idle_time(self):
        """Toggle the 'Idle Time' setting."""
        idle_time = not self.settings.get("idle_time", False)
        add_settings("idle_time", idle_time)
        self.idle_time_action.setChecked(idle_time)  # Update the checkbox state
        logger.info(f"Idle time set to {idle_time}")

    def toggle_day_schedule(self, day: str):
        """Toggle schedule for a specific day."""
        weekdays_schedule = self.settings.get('weekdays_schedule', {})
        current_state = weekdays_schedule.get(day, False)
        weekdays_schedule[day] = not current_state
        add_settings("weekdays_schedule", weekdays_schedule)
        logger.info(f"Schedule for {day} set to {not current_state}")

    def on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Context:
            self._build_rootmenu()  # Rebuild the context menu every time it's opened
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            open_webui(self.root_url)

# Quit the application properly
def quit_application() -> None:
    """Gracefully shut down the application."""
    logger.info("Shutting down...")
    manager.stop_all_watchers()
    logger.info("All watchers stopped.")
    time.sleep(2)
    QApplication.quit()  # Ensure the event loop quits
    sys.exit(0)

# Run the application
def run() -> int:
    """Initialize and run the PySide6 application."""
    logger.info("Starting application...")

    app = QApplication(sys.argv)

    scriptdir = Path(__file__).parent

    # Add search paths for icon resources
    QtCore.QDir.addSearchPath("icons", str(scriptdir.parent / "media/logo/"))
    QtCore.QDir.addSearchPath("icons", str(scriptdir.parent.parent / "Resources/sd_qt/media/logo/"))

    # Set up the tray icon
    if sys.platform == "darwin":
        icon = QIcon("icons:black-monochrome-logo.png")
        icon.setIsMask(True)  # Allow macOS to use filters for changing the icon's color
    else:
        icon = QIcon("icons:logo.png")

    if not icon.isNull():
        tray_icon = TrayIcon(icon)  # Create the tray icon
        tray_icon.show()

    QApplication.setQuitOnLastWindowClosed(False)

    logger.info("Application initialized successfully.")
    return app.exec()

if __name__ == "__main__":
    run()
