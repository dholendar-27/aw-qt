import sys
import logging
import subprocess
import webbrowser
from pathlib import Path
from PySide6.QtCore import QTimer, QDir
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PySide6.QtGui import QIcon, QAction
from .util import retrieve_settings, add_settings, user_status
from .manager import Manager

logger = logging.getLogger(__name__)

manager = Manager()

# Function to open URLs
def open_url(url: str) -> None:
    try:
        if sys.platform == "linux":
            subprocess.Popen(["xdg-open", url])
        else:
            webbrowser.open(url)
    except Exception as e:
        logger.error(f"Failed to open URL {url}: {e}")

def open_webui(root_url: str) -> None:
    """Open the web dashboard."""
    open_url(root_url)

def open_dir(d: str) -> None:
    """Open a directory in the system's default file manager."""
    try:
        if sys.platform == "win32":
            os.startfile(d)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", d])
        else:
            subprocess.Popen(["xdg-open", d])
    except Exception as e:
        logger.error(f"Failed to open directory {d}: {e}")

class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, parent: QWidget = None):
        super().__init__(icon, parent)
        self._parent = parent
        self.root_url = "http://localhost:7600"
        self.root_schedule = "http://localhost:7600/pages/settings"

        self.settings = {}
        self.user_status = user_status()
        self.previous_status = self.user_status

        self.activated.connect(self.on_activated)
        self._build_rootmenu()  # Initial menu setup

        # Timer for periodic user status checks
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_user_status)
        self.status_timer.start(60000)  # Every 60 seconds

    def _build_rootmenu(self):
        """Rebuild the context menu based on the current user status."""
        logger.debug("Rebuilding tray menu...")
        menu = QMenu(self._parent)

        try:
            self.settings = retrieve_settings()
        except Exception as e:
            logger.error(f"Failed to retrieve settings: {e}")
            self.settings = {}

        if self.settings:
            # User is logged in
            logger.debug("User is logged in. Building logged-in menu.")
            menu.addAction("Open Dashboard", lambda: open_webui(self.root_url))

            # Launch on Start
            self.launch_action = QAction("Launch on Start", self)
            self.launch_action.setCheckable(True)
            self.launch_action.setChecked(self.settings.get("launch", False))
            self.launch_action.triggered.connect(self.toggle_launch_on_start)
            menu.addAction(self.launch_action)

            # Enable Idle Time
            self.idle_time_action = QAction("Enable Idle Time", self)
            self.idle_time_action.setCheckable(True)
            self.idle_time_action.setChecked(self.settings.get("idle_time", False))
            self.idle_time_action.triggered.connect(self.toggle_idle_time)
            menu.addAction(self.idle_time_action)

            # Schedule Menu
            self.schedule_menu = QAction("Schedule", self)
            self.schedule_menu.triggered.connect(lambda: open_webui(self.root_schedule))
            menu.addAction(self.schedule_menu)
            menu.addSeparator()
        else:
            # User is not logged in
            logger.debug("User is not logged in. Building login menu.")
            menu.addAction("Login", lambda: open_webui(self.root_url))

        # Quit option (always available)
        menu.addAction("Quit", quit_application)

        self.setContextMenu(menu)

    def check_user_status(self):
        """Check if the user status has changed and rebuild the menu if needed."""
        try:
            logger.debug("Checking user status...")
            current_status = user_status()
            if current_status:
                logger.info(f"User status changed: {self.previous_status} -> {current_status}")
                self._build_rootmenu()  # Rebuild menu on status change
        except Exception as e:
            logger.error(f"Error checking user status: {e}")

    def toggle_launch_on_start(self):
        """Toggle the 'Launch on Start' setting."""
        try:
            launch_on_start = not self.settings.get("launch", False)
            add_settings("launch", launch_on_start)
            self.launch_action.setChecked(launch_on_start)
            logger.info(f"Launch on start set to {launch_on_start}")
        except Exception as e:
            logger.error(f"Failed to toggle Launch on Start: {e}")

    def toggle_idle_time(self):
        """Toggle the 'Idle Time' setting."""
        try:
            idle_time = not self.settings.get("idle_time", False)
            add_settings("idle_time", idle_time)
            self.idle_time_action.setChecked(idle_time)
            logger.info(f"Idle time set to {idle_time}")
        except Exception as e:
            logger.error(f"Failed to toggle Idle Time: {e}")

    def on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        print(f"Activated with reason: {reason}")

        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            logger.debug("Tray icon context menu activated.")
            self._build_rootmenu()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            logger.debug("Tray icon double-clicked. Opening dashboard.")
            open_webui(self.root_url)

def quit_application() -> None:
    """Gracefully shut down the application."""
    logger.info("Shutting down application...")
    try:
        manager.stop_all_watchers()
        logger.info("All watchers stopped.")
    except Exception as e:
        logger.error(f"Error stopping watchers: {e}")
    QApplication.quit()
    sys.exit(0)

def run() -> int:
    """Initialize and run the PySide6 application."""
    logger.info("Starting application...")

    app = QApplication(sys.argv)
    scriptdir = Path(__file__).parent

    # Add search paths for icon resources
    QDir.addSearchPath("icons", str(scriptdir.parent / "media/logo/"))
    QDir.addSearchPath("icons", str(scriptdir.parent.parent / "Resources/sd_qt/media/logo/"))

    # Set up the tray icon
    try:
        if sys.platform == "darwin":
            icon = QIcon("icons:black-monochrome-logo.png")
            icon.setIsMask(True)
        else:
            icon = QIcon("icons:logo.png")

        if not icon.isNull():
            tray_icon = TrayIcon(icon)
            tray_icon.show()
        else:
            logger.error("Failed to load tray icon.")
    except Exception as e:
        logger.error(f"Error initializing tray icon: {e}")

    QApplication.setQuitOnLastWindowClosed(False)
    logger.info("Application initialized successfully.")
    return app.exec()

if __name__ == "__main__":
    run()
