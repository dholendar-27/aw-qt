import os
import sys
import logging
import subprocess
import platform
import signal
import threading
from time import sleep
from typing import Optional

import requests

from sd_core.log import setup_logging
from sd_qt.keychain_script import clear_keys
from sd_qt.manager import Manager
from sd_qt.sd_desktop.main import run_application
from .config import AwQtSettings
from sd_qt.process_check import start_process_monitor

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """
    Configure the logging system for the application.
    """
    setup_logging("sd-qt", log_file=True)
    logger.info("Logging system configured")


def log_startup_message() -> None:
    """
    Logs a system startup message on macOS.
    """
    if platform.system() == "Darwin":
        subprocess.call("syslog -s 'sd-qt started'", shell=True)
        logger.info("Startup message logged to system log")


def setup_signal_handling(manager: Manager) -> None:
    """
    Sets up signal handling for Unix systems.
    """
    def handle_signal(signum, frame):
        logger.info(f"Signal {signum} received, shutting down gracefully...")
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    logger.info("Signal handlers configured")


def initialize_manager() -> Manager:
    """
    Initializes and returns the Manager instance.
    """
    logger.info("Initializing Manager")
    manager = Manager()
    manager.autostart(["sd-server"])
    logger.info("Manager initialized and autostarted processes")
    return manager


def run_monitoring_thread():
    """
    Starts the process monitoring thread.
    """
    logger.info("Starting process monitoring")
    start_process_monitor()


def main() -> None:
    """
    The main function of the application.
    """
    try:
        # Log startup messages and configure logging
        log_startup_message()
        configure_logging()
        logger.info("Application startup initiated")

        # Special handling for non-Windows platforms
        if sys.platform != "win32":
            try:
                os.setpgrp()
                logger.info("Process group set successfully")
            except PermissionError:
                logger.warning("Permission denied when trying to set process group")

        # Clear sensitive keys
        clear_keys()
        logger.info("Cleared sensitive keys")

        # Load application settings
        config = AwQtSettings()
        logger.info("Application settings loaded")

        # Initialize manager and start application
        manager = initialize_manager()
        run_application()
        logger.info("Application is running")

        # Start process monitoring
        run_monitoring_thread()

        # Handle platform-specific behavior
        if sys.platform == "win32":
            try:
                logger.info("Running on Windows, entering main sleep loop")
                sleep(threading.TIMEOUT_MAX)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down gracefully...")
        else:
            setup_signal_handling(manager)
            logger.info("Running on Unix-like platform, entering signal wait loop")
            signal.pause()

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Application has exited")


if __name__ == "__main__":
    main()
