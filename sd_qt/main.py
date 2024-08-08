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
from sd_qt.manager import Manager
from .config import AwQtSettings
from .sd_desktop.sundial import run_application

logger = logging.getLogger(__name__)

def check_server_status():
    try:
        $processName = "myprocess.exe"
$process = Get-Process | Where-Object { $_.ProcessName -eq $processName }

if ($process) {
    Write-Output "ERROR: Process $processName is running. Please close it before uninstalling."
    Exit 1
}  # Replace with your actual server health check endpoint
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.RequestException as e:
        logger.error(f"Error checking server status: {e}")
        return False

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
        
        manager.autostart(["sd-server"])
        # Check server status
        while not check_server_status():
            logger.info("Waiting for the server to start...")
            sleep(1)
        
        
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
