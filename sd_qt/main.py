import os
import sys
import logging
import subprocess
import platform
import signal
import threading
from typing import Optional
from time import sleep, time

import click
from sd_core.log import setup_logging

from .manager import Manager
from .config import AwQtSettings
from .sd_desktop.main import run_application

logger = logging.getLogger(__name__)

def main(
) -> None:

    """
    The main function of the application.

    @param testing: If True, tests will be run in a testing environment.
    @param verbose: If True, output will be written to stdout.
    @param autostart_modules: A comma-separated list of modules to autostart.
    @param no_gui: Don't display GUI to the user.
    @param interactive_cli: If True, interactive CLI will be used.

    @return: The exit code of the application or None if there was an error in the execution.
    """
    # Log startup message for debugging convenience on macOS
    if platform.system() == "Darwin":
        subprocess.call("syslog -s 'sd-qt started'", shell=True)

    # Setup logging
    setup_logging("sd-qt",log_file=True)
    logger.info("Started sd-qt...")

    # Log successful logging start for debugging convenience on macOS
    if platform.system() == "Darwin":
        subprocess.call("syslog -s 'sd-qt successfully started logging'", shell=True)

    # Create a process group, become its leader
    if sys.platform != "win32":
        try:
            os.setpgrp()
        except PermissionError:
            pass

    config = AwQtSettings()
    manager = Manager()
    manager.autostart(["sd-server"])
    sleep(10)
    run_application()

    if sys.platform == "win32":
        # Windows doesn't support signals, so we just sleep until interrupted
        try:
            sleep(threading.TIMEOUT_MAX)
        except KeyboardInterrupt:
            pass
    else:
        signal.pause()

    error_code = 0
    manager.stop_all()
    sys.exit(error_code)



