import sys
import logging
import subprocess
import webbrowser
import os
from pathlib import Path
from PySide6.QtCore import QTimer, QDir, Qt, QCoreApplication, QThread, Signal, QObject
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
from PySide6.QtGui import QIcon, QAction
from .util import retrieve_settings, add_settings, user_status, idletime_settings, launchon_start, signout, \
    cached_credentials
from .manager import Manager

# Initialize logger
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


class SignOutThread(QThread):
    finished = Signal()

    def run(self):
        """Handles sign-out process in the background."""
        try:
            signout()
            manager.stop_all_watchers()  # This may take time
            self.finished.emit()  # Emit signal when done
        except Exception as e:
            logger.error(f"Error during sign-out: {e}")
            self.finished.emit()


class LoginThread(QThread):
    finished = Signal()

    def run(self):
        """Handles the login process in the background."""
        try:
            open_webui("http://localhost:7600")  # Open the login URL
            self.finished.emit()  # Emit signal when done
        except Exception as e:
            logger.error(f"Error during login: {e}")
            self.finished.emit()


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
        self.update_menu()  # Build the menu initially

        # Timer for periodic user status checks
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_user_status)
        self.status_timer.start(60000)  # Every 60 seconds by default

        self.status_check_timer = QTimer(self)
        self.status_check_timer.timeout.connect(self.check_credentials_status)
        self.status_check_timer.stop()  # Initially stopped

        # Create background threads for login/signout
        self.sign_out_thread = None
        self.login_thread = None

    def update_menu(self):
        """Rebuild the tray menu based on the current user status."""
        menu = QMenu(self._parent)

        # Fetch the cached credentials safely
        self.credentials = cached_credentials()

        if self.credentials:
            # If credentials are valid, we can proceed to build the menu based on the logged-in user
            user_data = self.credentials.json() if hasattr(self.credentials, 'json') else self.credentials
            user_id = user_data.get("userId") if isinstance(user_data, dict) else None

            if user_id:
                # User is logged in
                self.settings = retrieve_settings()

                # Launch on Start action
                launch_action = QAction("Launch on Start", self)
                launch_action.setCheckable(True)
                launch_action.setChecked(self.settings.get("launch", False))
                launch_action.triggered.connect(self.toggle_launch_on_start)
                menu.addAction(launch_action)

                # Enable Idle Time action
                idle_time_action = QAction("Enable Idle Time", self)
                idle_time_action.setCheckable(True)
                idle_time_action.setChecked(self.settings.get("idle_time", False))
                idle_time_action.triggered.connect(self.toggle_idle_time)
                menu.addAction(idle_time_action)

                # Schedule Menu action
                schedule_menu = QAction("Schedule", self)
                schedule_menu.triggered.connect(lambda: open_webui(self.root_schedule))
                menu.addAction(schedule_menu)
                menu.addSeparator()

                # Sign Out action
                signout_action = QAction("Sign Out", self)
                signout_action.triggered.connect(self.sign_out)
                menu.addAction(signout_action)
            else:
                # If userId is missing or invalid, we show the Login option
                login_action = QAction("Login", self)
                login_action.triggered.connect(self.sign_in)
                menu.addAction(login_action)
        else:
            # If no credentials are found, show the Login option
            login_action = QAction("Sign in", self)
            login_action.triggered.connect(self.sign_in)
            menu.addAction(login_action)

        # Quit option
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(quit_action)

        # Set the tray menu
        self.setContextMenu(menu)

    def check_user_status(self):
        """Check if the user status has changed and rebuild the menu if needed."""
        try:
            current_status = user_status()
            if current_status != self.previous_status:
                self.previous_status = current_status
                self.update_menu()  # Refresh the menu immediately
        except Exception as e:
            logger.error(f"Error checking user status: {e}")

    def check_credentials_status(self):
        """Check the credentials every 2 seconds after login and update the menu once they are available."""
        try:
            self.credentials = cached_credentials()

            if self.credentials:
                # Stop the 2-second timer once the credentials are updated
                self.status_check_timer.stop()

                # Now switch to checking every 60 seconds
                self.status_timer.start(60000)  # Start the status timer again for 60 seconds

                # Rebuild the menu based on updated credentials
                self.update_menu()

                logger.info("Credentials updated, switching to 60-second checks.")
        except Exception as e:
            logger.error(f"Error checking credentials status: {e}")

    def toggle_launch_on_start(self):
        """Toggle the 'Launch on Start' setting."""
        try:
            launch_on_start = not self.settings.get("launch", False)
            launchon_start(launch_on_start)
            self.settings["launch"] = launch_on_start
            self.update_menu()
        except Exception as e:
            logger.error(f"Failed to toggle Launch on Start: {e}")

    def toggle_idle_time(self):
        """Toggle the 'Idle Time' setting."""
        try:
            idle_time = not self.settings.get("idle_time", False)
            self.settings["idle_time"] = idle_time
            idletime_settings()
            self.update_menu()
        except Exception as e:
            logger.error(f"Failed to toggle Idle Time: {e}")

    def sign_out(self):
        """Sign out the user and update the menu."""
        if not self.sign_out_thread or not self.sign_out_thread.isRunning():
            self.sign_out_thread = SignOutThread()
            self.sign_out_thread.finished.connect(self.on_sign_out_finished)
            self.sign_out_thread.start()

    def on_sign_out_finished(self):
        """Called when sign out is complete."""
        self.update_menu()  # Rebuild menu after signout

        # Explicitly update the context menu to reflect changes immediately
        self.setContextMenu(self._parent)  # Force the menu to refresh
        logger.info("Sign-out complete.")

    def sign_in(self):
        """Start the login process in the background."""
        if not self.login_thread or not self.login_thread.isRunning():
            self.login_thread = LoginThread()
            self.login_thread.finished.connect(self.on_login_finished)
            self.login_thread.start()

        # Start checking credentials every 2 seconds once login is initiated
        self.status_check_timer.start(2000)  # Check every 2 seconds after login

    def on_login_finished(self):
        """Handle login UI updates once login is complete."""
        self.update_menu()  # Rebuild the menu after successful login

        # Explicitly update the context menu to reflect changes immediately
        self.setContextMenu(self._parent)  # Force the menu to refresh
        logger.info("Login complete.")

    def on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            logger.info("Tray icon single-clicked.")
            # Action for single-click: open the web UI
            self.update_menu()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            logger.info("Tray icon double-clicked.")
            # Action for double-click: open the web UI
            open_webui(self.root_url)

    def quit_application(self):
        """Quit the application."""
        try:
            manager.stop_all()
        except Exception as e:
            logger.error(f"Error stopping watchers: {e}")
        QApplication.quit()
        sys.exit(0)


def run() -> int:
    """Initialize and run the PySide6 application."""
    app = QApplication(sys.argv)
    scriptdir = Path(__file__).parent

    # Add search paths for icon resources
    QDir.addSearchPath("icons", str(scriptdir.parent / "media/logo/"))
    QDir.addSearchPath("icons", str(scriptdir.parent.parent / "Resources/sd_qt/media/logo/"))

    # Set up the tray icon
    icon_path = "icons:black-monochrome-logo.png" if sys.platform == "darwin" else "icons:logo.png"
    icon = QIcon(icon_path)

    if icon.isNull():
        logger.error("Failed to load tray icon.")
        return -1

    # Create the tray icon
    tray_icon = TrayIcon(icon)

    tray_icon.show()
    QApplication.setQuitOnLastWindowClosed(False)
    return app.exec()


if __name__ == "__main__":
    run()
