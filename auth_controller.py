from flask import Blueprint, jsonify, request

from deep_face_model import verify_image, detect_is_same_person, check_is_smile
from firebase_util import upload_file_to_fire_storage
from utils import (
    create_thread_and_start,
    delete_file,
    create_temp_file_name,
    create_folder_if_not_exists,
    delete_folder,
)
import os

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET"])
def welcome():
    return jsonify({"message": "Hello, I am the auth service"})


def save_image_to_firebase(user_id, stage, error_type, file_path):
    create_thread_and_start(
        upload_file_to_fire_storage,
        (user_id, stage, error_type, file_path, "", "OpenDoorHistory", True),
    )


def authentication_stage(user_id, temp_file_name, retry_count=0):
    try:
        is_authorized = verify_image(temp_file_name, user_id)
        if not is_authorized:
            if retry_count < 3:
                folder_path = os.path.dirname(temp_file_name)
                delete_folder(folder_path)
            else:
                save_image_to_firebase(
                    user_id, "authentication", "is_authorized", temp_file_name
                )
        return jsonify(
            {
                "file_path": temp_file_name,
                "status": "authorized" if is_authorized else "unauthorized",
                "retry_count": retry_count if is_authorized else retry_count + 1,
            }
        )
    except Exception as e:
        delete_folder(os.path.dirname(temp_file_name))
        return jsonify({"status": "unauthorized", "error": str(e)}), 401


def smiling_stage(user_id, prev_file_path, current_file, retry_count=0):
    """
    prev_file_path: Đường dẫn tới file đã lưu tại bước authentication
    """
    # Lấy folder từ prev_file_path
    folder_path = os.path.dirname(prev_file_path)
    print(f"Folder path: {folder_path}")

    # Tạo file mới cho bước này
    temp_file_name = f"{folder_path}/smiling.jpg"
    current_file.save(temp_file_name)

    is_same_person = detect_is_same_person(prev_file_path, temp_file_name)
    if not is_same_person:
        if retry_count < 3:
            return jsonify(
                {"status": "not same person", "retry_count": retry_count + 1}
            )
        else:
            save_image_to_firebase(
                user_id, "smiling", "not same person", temp_file_name
            )
            return jsonify({"status": "unauthorized"})
    else:
        # Nếu là cùng một người, kiểm tra xem người đó có mỉm cười không
        is_smiling = check_is_smile(temp_file_name)
        if is_smiling:
            delete_folder(folder_path)
        elif retry_count < 3:
            delete_file(temp_file_name)

        if retry_count == 3 and not is_smiling:
            save_image_to_firebase(
                user_id, "smiling", "not smiling", temp_file_name
            )
            return jsonify({"status": "unauthorized"})

        return jsonify(
            {
                "status": ("smiling" if is_smiling else "not smiling"),
                "retry_count": retry_count if is_smiling else retry_count + 1,
            }
        )


@auth_bp.route("/verify", methods=["POST"])
def verify():
    file = request.files["file"]
    user_id = request.form["user_id"]
    stage = request.form["stage"]
    retry_count = int(request.form.get("retry_count", 0))

    if file.filename == "":
        return jsonify({"message": "No file selected for uploading"}), 400

    if stage == "authentication":
        folder_id = create_temp_file_name()
        folder_path = f"upload/{folder_id}"
        create_folder_if_not_exists(folder_path)
        temp_file_name = f"{folder_path}/{stage}.jpg"
        file.save(temp_file_name)

    if stage == "authentication":
        return authentication_stage(user_id, temp_file_name, retry_count)
    else:  # Check is smiling
        prev_file_path = request.form["prev_file_path"]
        return smiling_stage(user_id, prev_file_path, file, retry_count=retry_count)
