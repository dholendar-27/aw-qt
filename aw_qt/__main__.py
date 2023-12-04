import os
import sys
import ctypes
from aw_qt.main import main

def show_error_message():
    ctypes.windll.user32.MessageBoxW(0, "Sundial is already running.", "Sundial.exe", 0x10)

def check_lock_file(lock_file_path):
    if os.path.exists(lock_file_path):
        show_error_message()
        return True
    return False

def manage_lock_file(lock_file_path, create=False):
    try:
        if create:
            with open(lock_file_path, 'w') as lock_file:
                lock_file.write("")
        else:
            os.remove(lock_file_path)
    except Exception as e:
        print(e)
        return False
    return True



if sys.platform == "win32":
    lock_file_path = os.path.join(os.getenv('TEMP'), 'sundial.lock')
    if check_lock_file(lock_file_path):
        sys.exit(0)
    if manage_lock_file(lock_file_path, create=True):
        try:
            main()
        finally:
            manage_lock_file(lock_file_path)
elif sys.platform == "darwin":
    main()
