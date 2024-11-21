import sys
import logging
import os
import subprocess
import webbrowser
from typing import Any, Optional, Dict

from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QWidget,
)
import getpass
import time
from PySide6.QtGui import QIcon
# Assuming sd_core and other imports are correct
# import sd_core
from .manager import Manager, Module # Ensure this does not start the event loop

if sys.platform == "win32":
    import win32com.client

logger = logging.getLogger(__name__)

def get_env() -> Dict[str, str]:
    env = dict(os.environ)
    lp_key = "LD_LIBRARY_PATH"
    lp_orig = env.get(lp_key + "_ORIG")
    if lp_orig is not None:
        env[lp_key] = lp_orig
    else:
        env.pop(lp_key, None)
    return env

def open_url(url: str) -> None:
    if sys.platform == "linux":
        env = get_env()
        subprocess.Popen(["xdg-open", url], env=env)
    else:
        webbrowser.open(url)

def open_webui(root_url: str) -> None:
    print("Opening dashboard")
    open_url(root_url)

def open_apibrowser(root_url: str) -> None:
    print("Opening api browser")
    open_url(root_url + "/api")

def open_dir(d: str) -> None:
    if sys.platform == "win32":
        os.startfile(d)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", d])
    else:
        env = get_env()
        subprocess.Popen(["xdg-open", d], env=env)

def check_user_switch(manager: Manager) -> None:
    wmi = win32com.client.GetObject('winmgmts:')
    for session in wmi.InstancesOf('Win32_ComputerSystem'):
        if session.UserName is not None:
            time.sleep(3)
            username = session.UserName.split('\\')[-1]
            if username != getpass.getuser():
                logger.warning("Mismatch detected. Exiting...")
                exit(manager)

class TrayIcon(QSystemTrayIcon):
    def __init__(
            self,
            manager: Manager,
            icon: QIcon,
            parent: Optional[QWidget] = None,
            testing: bool = False,
    ) -> None:
        QSystemTrayIcon.__init__(self, icon, parent)
        self._parent = parent
        self.setToolTip("ActivityWatch" + (" (testing)" if testing else ""))

        self.manager = manager
        self.testing = testing

        self.root_url = f"http://localhost:{5666 if self.testing else 7600}"
        self.activated.connect(self.on_activated)

        self._build_rootmenu()

    def on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            open_webui(self.root_url)

    def _build_rootmenu(self) -> None:
        menu = QMenu(self._parent)

        if self.testing:
            menu.addAction("Running in testing mode")
            menu.addSeparator()

        menu.addAction("Open Sundial", lambda: run_application())
        menu.addSeparator()
        exitIcon = QIcon.fromTheme(
            "application-exit", QIcon("media/application_exit.png")
        )
        if exitIcon.availableSizes():
            menu.addAction(exitIcon, "Quit Sundial", lambda: exit(self.manager))
        else:
            menu.addAction("Quit Sundial", lambda: exit(self.manager))
        self.setContextMenu(menu)

    def _build_modulemenu(self, moduleMenu: QMenu) -> None:
        moduleMenu.clear()

        def add_module_menuitem(module: Module) -> None:
            title = module.name
            ac = moduleMenu.addAction(title, lambda: module.toggle(self.testing))
            ac.setData(module)
            ac.setCheckable(True)
            ac.setChecked(module.is_alive())

        for location, modules in [
            ("bundled", self.manager.modules_bundled),
            ("system", self.manager.modules_system),
        ]:
            header = moduleMenu.addAction(location)
            header.setEnabled(False)

            for module in sorted(modules, key=lambda m: m.name):
                add_module_menuitem(module)

def exit(manager: Manager) -> None:
    print("Shutdown initiated, stopping all services...")
    manager.stop_all()
    QApplication.quit()


if __name__ == "__main__":
    manager = Manager()  # Initialize your manager here
    sys.exit(run())  # Ensure the event loop is started only once
