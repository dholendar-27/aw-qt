import os
import sys
import logging
import subprocess
import platform
import signal
import threading
from time import sleep

from sd_core.log import setup_logging
from .manager import Manager
from .config import AwQtSettings
from .sd_desktop.sundial import run_application
from sd_qt.sd_desktop.sundialStartup import AppController

logger = logging.getLogger(__name__)
app = AppController()

def start_ui():
    try:
        app.start_ui()
    except Exception as e:
        logger.error(f"Error starting UI: {e}")

def stop_ui():
    try:
        app.stop_ui()
    except Exception as e:
        logger.error(f"Error stopping UI: {e}")

def main() -> None:
    """
    The main function of the application.
    """
    try:
        if platform.system() == "Darwin":
            subprocess.call("syslog -s 'sd-qt started'", shell=True)

        setup_logging("sd-qt", log_file=True)
        logger.info("Started sd-qt...")

        if platform.system() == "Darwin":
            subprocess.call("syslog -s 'sd-qt successfully started logging'", shell=True)

        if sys.platform != "win32":
            try:
                os.setpgrp()
            except PermissionError:
                logger.warning("Permission denied when trying to set process group")

        config = AwQtSettings()

        manager = Manager()
        start_ui()
        manager.autostart(["sd-server"])
        sleep(10)
        # stop_ui()
        print(121212112121)
        run_application()

        if sys.platform == "win32":
            try:
                sleep(threading.TIMEOUT_MAX)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, stopping...")
        else:
            def handle_signal(signum, frame):
                logger.info(f"Signal {signum} received, stopping...")
                manager.stop_all()
                stop_ui()
                sys.exit(0)

            signal.signal(signal.SIGTERM, handle_signal)
            signal.signal(signal.SIGINT, handle_signal)
            signal.pause()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
