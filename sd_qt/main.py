import os
import sys
import logging
import subprocess
import platform
import signal
import threading
import requests
from time import sleep

from sd_core.log import setup_logging
from sd_qt.keychain_script import clear_keys
from sd_qt.manager import Manager
from .config import AwQtSettings
from .sd_desktop.main import run_application

logger = logging.getLogger(__name__)

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

        clear_keys()

        config = AwQtSettings()

        manager = Manager()
        
        manager.autostart(["sd-server"])
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
                sys.exit(0)

            signal.signal(signal.SIGTERM, handle_signal)
            signal.signal(signal.SIGINT, handle_signal)
            signal.pause()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
