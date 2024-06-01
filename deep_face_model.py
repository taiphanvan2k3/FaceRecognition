from deepface import DeepFace
import os, time

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
model_name = "Facenet"


def preload_and_warmup():
    print("Loading model and performing warm-up...")
    start_time = time.time()

    # Thực hiện phân tích với một ảnh mẫu để làm nóng mô hình
    dummy_image_path = "test/dataset/tai.png"  # Đường dẫn tới ảnh mẫu
    DeepFace.analyze(dummy_image_path, actions=["emotion"])
    print("Warm-up completed in:", time.time() - start_time, "seconds")


def preload_model():
    print("Loading model and performing warm-up...")
    DeepFace.build_model(model_name)
    preload_and_warmup()


def detect_is_same_person(prev_img_path, smile_img_path):
    result = DeepFace.verify(
        prev_img_path,
        smile_img_path,
        model_name=model_name,
        distance_metric="euclidean_l2",
    )
    return result["distance"] <= 0.5


def check_is_smile(img_path):
    result = DeepFace.analyze(img_path, actions=["emotion"])[0]
    return result["emotion"]["happy"] >= 0.4


def verify_image(img_path, db_path):
    if "dataset" not in db_path:
        db_path = "dataset/" + db_path

    if not os.path.exists(db_path):
        return False

    result = DeepFace.find(
        img_path=img_path,
        db_path=db_path,
        model_name=model_name,
        distance_metric="euclidean_l2",
        threshold=0.5
    )
    if result[0].shape[0] == 0:
        return False
    return True
