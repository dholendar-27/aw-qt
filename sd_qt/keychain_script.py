import os
from sd_core.dirs import get_data_dir
from sd_core.cache import delete_password, clear_all_credentials, cache_user_credentials

# Get the data directory path
file_path = get_data_dir("sd-qt")

# Define the config file path for tracking deletion
config_file_path = os.path.join(file_path, "deletion_done.txt")  # Changed the file name here
CACHE_KEY = "Sundial"

# Function to delete data (passwords and credentials)
def delete_data():
    delete_password(CACHE_KEY)
    clear_all_credentials()
    
    # Check if credentials were successfully deleted
    if cache_user_credentials(CACHE_KEY) is None:
        return True
    else:
        return False

# Function to handle the deletion and file creation logic
def clear_keys():
    # Ensure the parent directory exists
    parent_dir = os.path.dirname(config_file_path)
    if not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir)  # Create the directory if it doesn't exist
            print(f"Created directory: {parent_dir}")
        except Exception as e:
            print(f"Error creating directory {parent_dir}: {e}")
            return

    # Now check for the marker file
    if not os.path.exists(config_file_path):
        # If deletion has not been done before, delete data
        if delete_data():
            # Create the marker file to indicate deletion has been completed
            try:
                with open(config_file_path, 'w') as f:
                    f.write("Data deletion completed on first run.")
                print("Data deletion completed and marker file created.")
            except Exception as e:
                print(f"Error creating marker file {config_file_path}: {e}")
        else:
            print("Failed to delete data or credentials.")
    else:
        print("Data has already been deleted. Skipping deletion.")

# Main execution
if __name__ == "__main__":
    clear_keys()
