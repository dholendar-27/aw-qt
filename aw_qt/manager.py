import configparser
import os
import signal
import sys
import logging
import subprocess
import platform
from pathlib import Path
from glob import glob
from time import sleep
from typing import Optional, List, Hashable, Set, Iterable

import psutil

import aw_core

logger = logging.getLogger(__name__)

# The path of aw_qt
_module_dir = os.path.dirname(os.path.realpath(__file__))

# The path of the aw-qt executable (when using PyInstaller)
_parent_dir = os.path.abspath(os.path.join(_module_dir, os.pardir))
config_file_path = os.path.join(os.path.dirname(os.path.abspath(os.path.join(_module_dir, os.pardir))), "process.ini")


def _log_modules(modules: List["Module"]) -> None:
    for m in modules:
        logger.debug(f" - {m.name} at {m.path}")


ignored_filenames = ["aw-cli", "aw-client", "aw-qt", "aw-qt.desktop", "aw-qt.spec"]
auto_start_modules = ["aw-server"]


def filter_modules(modules: Iterable["Module"]) -> Set["Module"]:
    # Remove things matching the pattern which is not a module
    # Like aw-qt itself, or aw-cli
    return {m for m in modules if m.name not in ignored_filenames}


def initialize_ini_file():
    """
    Initialize the INI file with default values if it doesn't exist.
    """
    if not os.path.exists(config_file_path):
        config = configparser.ConfigParser()
        # Adding sections and default values for each module
        config['aw-server'] = {'status': 'False', 'pid': 0}
        config['aw-watcher-afk'] = {'status': 'False', 'pid': 0}
        config['aw-watcher-window'] = {'status': 'False', 'pid': 0}

        with open(config_file_path, 'w') as configfile:
            config.write(configfile)
        logger.info("Initialized new INI file with default values.")


def is_executable(path: str, filename: str) -> bool:
    if not os.path.isfile(path):
        return False
    # On windows all files ending with .exe are executables
    if platform.system() == "Windows":
        return filename.endswith(".exe")
    # On Unix platforms all files having executable permissions are executables
    # We do not however want to include .desktop files
    else:  # Assumes Unix
        if not os.access(path, os.X_OK):
            return False
        if filename.endswith(".desktop"):
            return False
        return True


def _discover_modules_in_directory(path: str) -> List["Module"]:
    """Look for modules in given directory path and recursively in subdirs matching aw-*"""
    modules = []
    matches = glob(os.path.join(path, "aw-*"))
    for path in matches:
        basename = os.path.basename(path)
        if is_executable(path, basename) and basename.startswith("aw-"):
            name = _filename_to_name(basename)
            modules.append(Module(name, Path(path), "bundled"))
        elif os.path.isdir(path) and os.access(path, os.X_OK):
            modules.extend(_discover_modules_in_directory(path))
        else:
            logger.warning(f"Found matching file but was not executable: {path}")
    return modules


def _filename_to_name(filename: str) -> str:
    return filename.replace(".exe", "")


def _discover_modules_bundled() -> List["Module"]:
    """Use ``_discover_modules_in_directory`` to find all bundled modules"""
    search_paths = [_module_dir, _parent_dir]
    if platform.system() == "Darwin":
        macos_dir = os.path.abspath(os.path.join(_parent_dir, os.pardir, "MacOS"))
        search_paths.append(macos_dir)
    # logger.debug(f"Searching for bundled modules in: {search_paths}")

    modules: List[Module] = []
    for path in search_paths:
        modules += _discover_modules_in_directory(path)

    modules = list(filter_modules(modules))
    logger.info(f"Found {len(modules)} bundled modules")
    _log_modules(modules)
    return modules


def _discover_modules_system() -> List["Module"]:
    """Find all aw- modules in PATH"""
    search_paths = os.get_exec_path()

    # Needed because PyInstaller adds the executable dir to the PATH
    if _parent_dir in search_paths:
        search_paths.remove(_parent_dir)

    # logger.debug(f"Searching for system modules in PATH: {search_paths}")
    modules: List["Module"] = []
    paths = [p for p in search_paths if os.path.isdir(p)]
    for path in paths:
        try:
            ls = os.listdir(path)
        except PermissionError:
            logger.warning(f"PermissionError while listing {path}, skipping")
            continue

        for basename in ls:
            if not basename.startswith("aw-"):
                continue
            if not is_executable(os.path.join(path, basename), basename):
                continue
            name = _filename_to_name(basename)
            # Only pick the first match (to respect PATH priority)
            if name not in [m.name for m in modules]:
                modules.append(Module(name, Path(path) / basename, "system"))

    modules = list(filter_modules(modules))
    logger.info(f"Found {len(modules)} system modules")
    _log_modules(modules)
    return modules


def read_update_ini_file(modules, key, new_value=None):
    """
    Read and optionally update data in an INI file.

    Args:
        file_path (str): The path to the INI file.
        section (str): The section in the INI file.
        key (str): The key within the section.
        new_value (str, optional): The new value to set for the key (if None, no update is performed).

    Returns:
        str: The current value of the key in the specified section.
    """
    config = configparser.ConfigParser()
    config.read(config_file_path)

    # Read data from the INI file
    current_value = config.get(modules, key)

    if new_value is not None:
        # Update data in the INI file if new_value is provided
        config.set(modules, key, new_value)
        with open(config_file_path, 'w') as configfile:
            config.write(configfile)

    return current_value


class Module:
    def __init__(self, name: str, path: Path, type: str) -> None:
        self.name = name
        self.path = path
        assert type in ["system", "bundled"]
        self.type = type
        self.config_file_path = config_file_path
        self.started = False
        initialize_ini_file()

    def _read_pid(self) -> Optional[int]:
        config = configparser.ConfigParser()
        config.read(self.config_file_path)
        try:
            return int(config.get(self.name, 'pid'))
        except Exception as e:
            logger.error(f"Error reading PID for {self.name}: {e}")
            return None

    def _write_pid(self, pid: int):
        config = configparser.ConfigParser()
        config.read(self.config_file_path)
        if not config.has_section(self.name):
            config.add_section(self.name)
        config.set(self.name, 'pid', str(pid))
        with open(self.config_file_path, 'w') as configfile:
            config.write(configfile)
        logger.debug(f"PID for {self.name} written to file: {pid}")

    def _update_status_in_ini(self, status: bool):
        config = configparser.ConfigParser()
        config.read(self.config_file_path)
        if not config.has_section(self.name):
            config.add_section(self.name)
        config.set(self.name, 'status', 'True' if status else 'False')
        with open(self.config_file_path, 'w') as configfile:
            config.write(configfile)

    def _is_process_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def start(self):
        pid = self._read_pid()
        if pid and self._is_process_running(pid):
            logger.info(f"{self.name} is already running")
            return

        self.started = True
        logger.info(f"Starting {self.name}")
        self._process = subprocess.Popen([str(self.path)], start_new_session=True)
        self._write_pid(self._process.pid)
        self._update_status_in_ini(True)

    def stop(self):
        pid = self._read_pid()
        if pid and self._is_process_running(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Stopped {self.name}")
                self.started = False
                self._update_status_in_ini(False)  # Update status to False when stopped
                self._write_pid(0)  # Remove the PID from the INI file
            except OSError as e:
                logger.error(f"Error stopping {self.name}: {e}")
        else:
            logger.info(f"{self.name} is not running or PID is invalid")

    def is_alive(self) -> bool:
        pid = self._read_pid()
        if pid == 0 or pid is None:
            return False

        # Check if a process with this PID exists
        if not psutil.pid_exists(pid):
            return False

        # Validate if the process is the correct one
        try:
            proc = psutil.Process(pid)
            # You can add more checks here if needed, like comparing process names
            return proc.is_running()
        except psutil.NoSuchProcess:
            return False

    def toggle(self, testing: bool) -> None:
        if self.started:
            self.stop()
        else:
            self.start()

    def read_log(self, testing: bool) -> str:
        """Useful if you want to retrieve the logs of a module"""
        log_path = aw_core.log.get_latest_log_file(self.name, testing)
        if log_path:
            with open(log_path) as f:
                return f.read()
        else:
            return "No log file found"


class Manager:
    def __init__(self, testing: bool = False) -> None:
        self.modules: List[Module] = []
        self.testing = testing

        self.discover_modules()

    @property
    def modules_system(self) -> List[Module]:
        return [m for m in self.modules if m.type == "system"]

    @property
    def modules_bundled(self) -> List[Module]:
        return [m for m in self.modules if m.type == "bundled"]

    def discover_modules(self) -> None:
        # These should always be bundled with aw-qt
        modules = set(_discover_modules_bundled())
        modules |= set(_discover_modules_system())
        modules = filter_modules(modules)

        # update one by one
        for m in modules:
            if m not in self.modules:
                self.modules.append(m)

    def get_unexpected_stops(self) -> List[Module]:
        return list(filter(lambda x: x.started and not x.is_alive(), self.modules))

    def start(self, module_name: str) -> None:
        # NOTE: Will always prefer a bundled version, if available. This will not affect the
        #       aw-qt menu since it directly calls the module's start() method.
        bundled = [m for m in self.modules_bundled if m.name == module_name]
        system = [m for m in self.modules_system if m.name == module_name]
        if bundled:
            bundled[0].start()
        elif system:
            system[0].start()
        else:
            logger.error(f"Manager tried to start nonexistent module {module_name}")

    def autostart(self, autostart_modules: List[str]) -> None:
        # NOTE: Currently impossible to autostart a system module if a bundled module with the same name exists

        # We only want to autostart modules that are both in found modules and are asked to autostart.
        for name in autostart_modules:
            if name not in [m.name for m in self.modules]:
                logger.error(f"Module {name} not found")
        autostart_modules = list(set(autostart_modules))

        # Start aw-server-rust first
        if "aw-server-rust" in autostart_modules:
            self.start("aw-server-rust")
        elif "aw-server" in autostart_modules and "aw-server" in auto_start_modules:
            self.start("aw-server")

        autostart_modules = list(
            set(autostart_modules) - {"aw-server"}
        )
        for name in autostart_modules:
            if name in auto_start_modules:
                self.start(name)

    def stop(self, module_name: str) -> None:
        for m in self.modules:
            if m.name == module_name:
                m.stop()
                break
        else:
            logger.error(f"Manager tried to stop nonexistent module {module_name}")

    def stop_all(self) -> None:
        server_module_name = "aw-server"
        server_module = None

        # Find 'aw-server' module and temporarily exclude it from the stop process
        for module in self.modules:
            if module.name == server_module_name:
                server_module = module
            elif module.is_alive():
                module.stop()

        # Finally, stop 'aw-server' if it's running
        if server_module and server_module.is_alive():
            server_module.stop()

    def print_status(self, module_name: Optional[str] = None) -> None:
        header = "name                status      type"
        if module_name:
            # find module
            module = next((m for m in self.modules if m.name == module_name), None)
            if module:
                logger.info(header)
                self._print_status_module(module)
            else:
                logger.error(f"Module {module_name} not found")
        else:
            logger.info(header)
            for module in self.modules:
                self._print_status_module(module)

    def _print_status_module(self, module: Module) -> None:
        logger.info(
            f"{module.name:18}  {'running' if module.is_alive() else 'stopped' :10}  {module.type}"
        )

    def status(self):
        modules_list = []
        # Serialize module data
        for m in self.modules:
            module_info = {
                "watcher_name": m.name,  # Replace with the actual attribute or property name
                "Watcher_status": m.is_alive(),  # Replace with the actual method or property
                "Watcher_location": str(m)  # Convert module object to a string
            }
            modules_list.append(module_info)
        return modules_list

    def stop_modules(self, module_name: str) -> str:
        for m in self.modules:
            if m.name == module_name:
                m.stop()
                return f"Module {module_name} is stopped"
        else:
            return f"Manager tried to stop nonexistent module {module_name}"


def main_test():
    manager = Manager()
    for module in manager.modules:
        module.start(testing=True)
        sleep(2)
        assert module.is_alive()
        module.stop()


if __name__ == "__main__":
    main_test()
