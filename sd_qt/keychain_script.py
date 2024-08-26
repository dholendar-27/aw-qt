import os
from sd_core.dirs import get_data_dir
from sd_core.cache import delete_password, clear_all_credentials, cache_user_credentials

file_path = get_data_dir("sd-qt")
config_file_path = os.path.join(file_path, "deletion_done.txt")


def delete_data():
    delete_password("SD_KEYS")
    clear_all_credentials()
    if cache_user_credentials("SD_KEYS") == None:
        return True
    else:
        return False

def clear_keys():
    if not os.path.exists(config_file_path):
        # Delete the data
        if delete_data():
            # Create the marker file to indicate deletion has been done
            with open(config_file_path, 'w') as f:
                f.write("Data deletion completed on first run.")
        else:
            return
    else:
        print("Data has already been deleted. Skipping deletion.")

if __name__ == "__main__":
    clear_keys()
