import threading
from datetime import datetime
import os, shutil


def create_temp_file_name():
    # Lấy thời gian hiện tại
    now = datetime.now()
    timestamp_str = now.strftime("%Y%m%d%H%M%S")

    return timestamp_str


def create_folder_if_not_exists(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def delete_file(file_name):
    os.remove(file_name)


def delete_folder(folder_name):
    if os.path.exists(folder_name) and os.path.isdir(folder_name):
        shutil.rmtree(folder_name)
        print(f"Folder '{folder_name}' has been deleted.")
    else:
        print(f"Folder '{folder_name}' does not exist or is not a directory.")


def create_thread_and_start(target, args):
    thread = threading.Thread(target=target, args=args)
    thread.start()
    return thread
