import os
import sys
import logging
import subprocess
import platform
import signal
import threading
from typing import Optional
from time import sleep

import click
from sd_core.log import setup_logging
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMessageBox,
    QMenu,
    QWidget,
    QPushButton,
)
from PyQt6.QtGui import QIcon
from pathlib import Path

from .manager import Manager
from .config import AwQtSettings
from .sd_onboard_screens import main_method, user_cancelled

logger = logging.getLogger(__name__)

@click.command("sd-qt", help="A trayicon and service manager for ActivityWatch")
@click.option(
    "--testing", is_flag=True, help="Run the trayicon and services in testing mode"
)
@click.option("-v", "--verbose", is_flag=True, help="Run with debug logging")
@click.option(
    "--autostart-modules",
    help="A comma-separated list of modules to autostart, or just `none` to not autostart anything.",
)
@click.option(
    "--no-gui",
    is_flag=True,
    help="Start sd-qt without a graphical user interface (terminal output only)",
)
@click.option(
    "-i",
    "--interactive",
    "interactive_cli",
    is_flag=True,
    help="Start sd-qt in interactive cli mode (forces --no-gui)",
)
def main(
    testing: bool,
    verbose: bool,
    autostart_modules: Optional[str],
    no_gui: bool,
    interactive_cli: bool,
) -> None:
    """
    The main function of the application. This is called by the :py:func:`~app.main` function to start the application

    @param testing - If True tests will be run in a testing environment
    @param verbose - If True the output will be written to stdout
    @param autostart_modules - A list of modules to autostart
    @param no_gui - Don't display GUI to the user
    @param interactive_cli - If True interactive CLI will be used

    @return The exit code of the application or None if there was an error in the execution of the application (in which case it will be 0)
    """
    # Since the .app can crash when started from Finder for unknown reasons, we send a syslog message here to make debugging easier.
    # This function is called by the sd qt daemon when the OS is Darwin.
    
    setup_logging("sd-qt", testing=testing, verbose=verbose, log_file=True)
    logger.info("Started sd-qt...")

    if sys.platform == "win32":
            app_dir = os.path.expanduser("~")
            install_flag_file = os.path.join(app_dir, "AppData", "Local", "Sundial", "Sundial", "sd-qt", "flag.txt")

    # Check if the flag file exists and its content
    if not os.path.exists(install_flag_file):
        try:
        # pylint: disable=import-outside-toplevel
            main_return_code = main_method()
            if main_return_code == 0:
                logger.error("User cancelled the operation in GUI.")
                return 1  # Exit main() with error code if GUI operation was cancelled
            # Ensure global flag is accessed correctly
            # Create the flag file to indicate that the application has been installed
            os.makedirs(os.path.dirname(install_flag_file), exist_ok=True)
            with open(install_flag_file, 'w') as f:
                f.write("1")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        return 0
    else:
        logger.info("Application has already been installed and continue ....")
    if platform.system() == "Darwin":
        subprocess.call("syslog -s 'sd-qt started'", shell=True)

    # Since the .app can crash when started from Finder for unknown reasons, we send a syslog message here to make debugging easier.
    if platform.system() == "Darwin":
        subprocess.call("syslog -s 'sd-qt successfully started logging'", shell=True)

    # Create a process group, become its leader
    # TODO: This shouldn't go here
    if sys.platform != "win32":
        try:
            os.setpgrp()
        except PermissionError:
            pass

    config = AwQtSettings(testing=testing)
    _autostart_modules = (
        [m.strip() for m in autostart_modules.split(",") if m and m.lower() != "none"]
        if autostart_modules
        else config.autostart_modules
    )
    manager = Manager(testing=testing)
    manager.autostart(_autostart_modules)

    # Run trayicon if no_gui is set to true and interactive_cli is set to true.
    if not no_gui and not interactive_cli:
        from . import trayicon  # pylint: disable=import-outside-toplevel
        error_code = trayicon.run(manager, testing=testing)
    elif interactive_cli:
        _interactive_cli(manager)
        error_code = 0
    else:
        if sys.platform == "win32":
            try:
                sleep(threading.TIMEOUT_MAX)
            except KeyboardInterrupt:
                pass
        else:
            signal.pause()

        error_code = 0

    manager.stop_all()
    sys.exit(error_code)

def _interactive_cli(manager: Manager) -> None:
    """
     Interactive CLI for this module. This is a helper function to interactively call the manager's start () and stop () methods with the manager passed as an argument
     
     @param manager - The manager to use for
    """
    # input q and print the command line input
    while True:
        answer = input("> ")
        # if answer is q or q
        if answer == "q":
            break

        tokens = answer.split(" ")
        t = tokens[0]
        # This function is called by the manager.
        if t == "start":
            # Start the module if the first token is a token.
            if len(tokens) == 2:
                manager.start(tokens[1])
            else:
                print("Usage: start <module>")
        elif t == "stop":
            # Stop the module if the first token is a token.
            if len(tokens) == 2:
                manager.stop(tokens[1])
            else:
                print("Usage: stop <module>")
        elif t in ["s", "status"]:
            # Prints the status of the tokens.
            if len(tokens) == 1:
                manager.print_status()
            elif len(tokens) == 2:
                manager.print_status(tokens[1])
        elif not t.strip():
            # if t was empty string, or just whitespace, pretend like we didn't see that
            continue
        else:
            print(f"Unknown command: {t}")