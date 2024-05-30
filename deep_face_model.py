from deepface import DeepFace
import os

model_name = "Facenet"


def preload_model():
    DeepFace.build_model("Emotion")
    DeepFace.build_model(model_name)


def detect_is_same_person(prev_img_path, smile_img_path):
    result = DeepFace.verify(
        prev_img_path,
        smile_img_path,
        model_name=model_name,
        distance_metric="euclidean_l2",
    )
    return result["distance"] <= 0.4


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
    )
    if result[0].shape[0] == 0:
        return False
    return True
