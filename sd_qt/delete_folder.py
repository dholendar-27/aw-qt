import os
import shutil
import platform
from pathlib import Path

# Define the package name dynamically
def set_package_name(package_name):
    global current_package_name
    current_package_name = package_name

# Get the package's first run flag path
def get_first_run_flag_path():
    if platform.system() == "Darwin":  # macOS
        # Store in the user's home directory, as a hidden file
        user_home = str(Path.home())
        return Path(user_home) / f".{current_package_name}_first_run.txt"
    elif platform.system() == "Windows":  # Windows
        # Store in AppData\Local folder as a hidden file
        appdata_local = Path(os.getenv("LOCALAPPDATA"))
        return appdata_local / current_package_name / "first_run_flag.txt"

# Hide the file in a secure location
def hide_file(file_path):
    if platform.system() == "Windows":
        # Set the hidden attribute for Windows
        try:
            os.system(f"attrib +h {file_path}")
        except Exception as e:
            print(f"Failed to hide file on Windows: {e}")
    elif platform.system() == "Darwin":
        # For macOS, we ensure the file is hidden by using the dot (.) prefix
        pass  # macOS automatically treats files starting with a dot as hidden

# Delete .db files in the specified directory
def delete_db_files(directory_path):
    print(f"Deleting .db files in {directory_path}...")
    if directory_path.exists():
        # Find and delete all .db files in the directory
        for db_file in directory_path.glob("*.db"):
            try:
                db_file.unlink()  # Delete the file
                print(f"Deleted database file: {db_file}")
            except Exception as e:
                print(f"Failed to delete {db_file}: {e}")
    else:
        print(f"Directory not found: {directory_path}")

# Check if it's the first time running the app by checking a secure hidden file
def is_first_run():
    first_run_flag = get_first_run_flag_path()
    print(f"Checking first run flag: {first_run_flag}")
    return not first_run_flag.exists()

# Set the flag that the app has run before (create the hidden file)
def set_first_run_flag():
    first_run_flag = get_first_run_flag_path()
    first_run_flag.touch()  # Create the file
    hide_file(first_run_flag)  # Ensure the file is hidden
    print(f"First run flag set: {first_run_flag}")

# Reset the application (delete existing first-run flag)
def reset_application():
    print("Resetting the application...")
    first_run_flag = get_first_run_flag_path()
    if first_run_flag.exists():
        try:
            first_run_flag.unlink()  # Delete the first-run flag file
            print(f"Deleted first-run flag: {first_run_flag}")
        except Exception as e:
            print(f"Failed to delete first-run flag: {e}")

# Main function to handle first run or reinstall
def handle_first_run(package_name, reset_on_reinstall=False):
    set_package_name(package_name)  # Set the package name dynamically
    
    if reset_on_reinstall:
        # If it's a reinstall, reset the app to treat it like a fresh install
        reset_application()
    
    if is_first_run():
        print(f"First time running {package_name}. Skipping folder deletion.")
        # Folder deletion step removed here
        set_first_run_flag()
    else:
        print(f"Not the first time running {package_name}. Skipping folder deletion.")
    
    # Additional cleanup: delete .db files
    if platform.system() == "Windows":
        sd_server_path = Path(os.getenv("LOCALAPPDATA")) / "Sundial/Sundial/sd-server"
    else:
        sd_server_path = Path.home() / "Library/Application Support/Sundial/sd-server"  # macOS

    print(f"Deleting .db files in {sd_server_path}...")
    delete_db_files(sd_server_path)

# Run the function on application startup
if __name__ == "__main__":
    package_name = "Sundial"  # You can change this to any package name
    reset_on_reinstall = True  # Set to True to reset on reinstall
    handle_first_run(package_name, reset_on_reinstall)
