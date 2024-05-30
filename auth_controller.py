from flask import Blueprint, jsonify, request
from datetime import datetime
from deep_face_model import verify_image, detect_is_same_person, check_is_smile
import os, shutil

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET"])
def welcome():
    return jsonify({"message": "Hello, I am the auth service"})


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


def authentication_stage(temp_file_name, user_id, retry_count=0):
    try:
        is_authorized = verify_image(temp_file_name, user_id)
        if not is_authorized:
            delete_file(temp_file_name)
        return jsonify(
            {
                "file_path": temp_file_name,
                "status": "authorized" if is_authorized else "unauthorized",
                "retry_count": retry_count if is_authorized else retry_count + 1,
            }
        )
    except Exception as e:
        delete_folder(os.path.dirname(temp_file_name))
        return jsonify({"status": "unauthorized", "error": str(e)})


def smiling_stage(prev_file_path, current_file, retry_count=0):
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
            return (
                jsonify({"status": "not same person", "retry_count": retry_count + 1}),
                401,
            )
        else:
            delete_folder(folder_path)
            return jsonify({"status": "unauthorized"})
    else:
        # Nếu là cùng một người, kiểm tra xem người đó có mỉm cười không
        is_smiling = check_is_smile(temp_file_name)
        if is_smiling:
            delete_folder(folder_path)
        else:
            delete_file(temp_file_name)

        if retry_count == 3 and not is_smiling:
            delete_folder(folder_path)
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
        return authentication_stage(temp_file_name, user_id, retry_count)
    else:  # Check is smiling
        prev_file_path = request.form["prev_file_path"]
        return smiling_stage(prev_file_path, file, retry_count=retry_count)
