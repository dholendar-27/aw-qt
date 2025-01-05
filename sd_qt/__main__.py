import os
import sys
import tempfile
import ctypes
from sd_qt.main import main
from sd_qt.delete_folder import handle_first_run

def show_error_message():
    ctypes.windll.user32.MessageBoxW(
        0, "Sundial is already running.", "Sundial.exe", 0x10)


tempdir = tempfile.gettempdir()
lockfile = os.sep.join([tempdir, 'myapp.lock'])
try:
    if os.path.isfile(lockfile):
        os.unlink(lockfile)
# Should give you smth like 'WindowsError: [Error 32] The process cannot access the file because it is being used by another process..'
except WindowsError as e:
    ctypes.windll.user32.MessageBoxW(0,
                                     "Sundial is already running.",
                                     "Sundial.exe",
                                     0x10)
    sys.exit(0)

with open(lockfile, 'wb') as lockfileobj:
    # run your app's main here
    package_name = "Sundial"  # You can change this to any package name
    reset_on_reinstall = True  # Set to True to reset on reinstall
    handle_first_run(package_name, reset_on_reinstall)
    main()
os.unlink(lockfile)
