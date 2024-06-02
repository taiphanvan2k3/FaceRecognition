from firebase_admin import credentials, firestore, initialize_app, get_app, storage
from firebase_admin.auth import create_custom_token
import os, socket
from utils import delete_folder, create_temp_file_name
from dotenv import load_dotenv

load_dotenv()


def initialize_firestore():
    try:
        # Kiểm tra xem ứng dụng Firebase đã được khởi tạo chưa
        get_app()
    except Exception as e:
        # Nếu chưa, khởi tạo nó
        current_dir = os.path.dirname(os.path.realpath(__file__))
        cred = credentials.Certificate(f"{current_dir}/key.json")
        initialize_app(
            cred,
            {"storageBucket": os.getenv("STORAGE_BUCKET")},
        )
        print("Initialize: Firebase app has been initialized.")
    return firestore.client()


db = initialize_firestore()


def save_open_door_history(user_id, stage, error_type, image_url):
    open_door_history_ref = db.collection("OpenDoorHistory")
    open_at = firestore.SERVER_TIMESTAMP
    open_door_history_ref.add(
        {
            "user_id": user_id,
            "stage": stage,
            "error_type": error_type,
            "image_url": image_url,
            "open_at": open_at,
        }
    )
    print("Done save open door history.")


def upload_file_to_fire_storage(
    user_id, stage, error_type, file_path, file_name="", bucket_name="", is_delete=False
):
    bucket = storage.bucket()
    if file_name == "":
        file_name = f"{create_temp_file_name()}.jpg"
    blob_name = f"{bucket_name}/{file_name}"
    blob = bucket.blob(blob_name)

    # Tạo access token
    token = create_custom_token("<uid>")

    # Thêm token vào header của yêu cầu tải lên
    blob.metadata = {"customMetadata": {"FirebaseStorageDownloadTokens": token}}
    blob.upload_from_filename(file_path)
    blob.make_public()

    print(f"Done upload {file_name} to {bucket_name}.")

    if is_delete:
        folder_path = os.path.dirname(file_path)
        delete_folder(folder_path)

    public_url = blob.public_url
    save_open_door_history(user_id, stage, error_type, public_url)

    return blob.public_url


def save_server_ip():
    hostname = socket.gethostname()
    IP_address = socket.gethostbyname(hostname)

    # Lưu vào realtime database
    server_info_ref = (
        initialize_firestore().collection("ServerInfo").document("server_ip")
    )
    server_info_ref.set({"ip": IP_address})
    print("URL server: ", IP_address)

def save_task_schedule(id, action, hour, minute):
    task_schedule_ref = db.collection("TaskSchedule")
    task_schedule_ref.add(
        {
            "id": id,
            "action": action,
            "hour": hour,
            "minute": minute,
        }
    )
    print("Done save task schedule.")