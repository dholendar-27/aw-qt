from aw_qt.main import main
import os
import sys
import ctypes

def check_lock_file(lock_file_path):
    if os.path.exists(lock_file_path):
        ctypes.windll.user32.MessageBoxW(0, 
                                         "Sundial is already running.", 
                                         "Sundial.exe", 
                                         0x10)  # 0x10 is the code for an error icon
        return True
    return False

def create_lock_file(lock_file_path):
    try:
        with open(lock_file_path, 'w') as lock_file:
            lock_file.write("")
    except Exception as e:
        print(e)
        return False
    return True

def delete_lock_file(lock_file_path):
    try:
        os.remove(lock_file_path)
    except Exception as e:
        print(e)


lock_file_path = os.path.join(os.getenv('TEMP'), 'sundail.lock')

if check_lock_file(lock_file_path):
    sys.exit(0)

if create_lock_file(lock_file_path):
    try:
        main()
    finally:
        delete_lock_file(lock_file_path)


