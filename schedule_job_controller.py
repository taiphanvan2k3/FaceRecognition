from flask import Blueprint, Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit, requests
from firebase_util import initialize_firestore

app = Flask(__name__)

firebase_db = initialize_firestore()
scheduled_jobs_collection = firebase_db.collection("ScheduledJobs")

# Khởi tạo BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Đảm bảo scheduler dừng khi ứng dụng Flask dừng
atexit.register(lambda: scheduler.shutdown())

is_loaded_stored_tasks = False
schedule_job_bp = Blueprint("schedule_job", __name__)


# Load các tasks đã lưu trong DB mỗi khi run lại server
def load_tasks():
    with app.app_context():
        global is_loaded_stored_tasks
        if is_loaded_stored_tasks:
            return
        tasks = firebase_db.collection("ScheduledJobs").get()
        for task in tasks:
            task_data = task.to_dict()
            scheduler.add_job(
                func=scheduled_task,
                trigger=CronTrigger(
                    hour=task_data.get("hour"),
                    minute=task_data.get("minute"),
                    day="*",
                    month="*",
                    year="*",
                ),
                args=[task.id],
                id=task.id,
            )
        is_loaded_stored_tasks = True


# Hàm nhiệm vụ bạn muốn chạy theo lịch
def scheduled_task(task_id):
    with app.app_context():
        task = scheduled_jobs_collection.document(task_id).get().to_dict()
        if task:
            task_action = task.get("action")
            print("Running task", task_action)
            base_url = (
                "http://localhost:9999"  # Đảm bảo sử dụng URL của server Flask của bạn
            )

            if task_action == "turn on led home":
                url = f"{base_url}/led?location=living-room&status=1"
            elif task_action == "turn on led garden":
                url = f"{base_url}/led?location=garden&intensity=255"
            elif task_action == "turn on fan":
                url = f"{base_url}/fan?location=living-room&status=1"
            else:
                print(f"Unknown task action: {task_action}")
                return

            # Gửi yêu cầu HTTP
            response = requests.get(url)
            print(f"Requested {url}, response status code: {response.status_code}")


# Tạo bảng trong cơ sở dữ liệu và load tasks khi khởi động
with app.app_context():
    # db.create_all()
    load_tasks()


@schedule_job_bp.route("/schedule", methods=["POST"])
def schedule_task():
    data = request.get_json()
    action = data.get("action")
    hour = data.get("hour")
    minute = data.get("minute")

    # Lưu thông tin nhiệm vụ vào Firebase
    new_scheduled_job = scheduled_jobs_collection.add(
        {
            "action": action,
            "hour": hour,
            "minute": minute,
        }
    )

    task_id = new_scheduled_job[1].id

    # Thêm nhiệm vụ vào scheduler
    scheduler.add_job(
        func=scheduled_task,
        trigger=CronTrigger(
            hour=hour, minute=minute, day="*", month="*", year="*"
        ),  # Chạy vào mỗi giờ và phút cố định
        args=[task_id],
        id=task_id,
    )

    return (
        jsonify({"message": "Add Job successfully!", "task_id": task_id}),
        200,
    )


@schedule_job_bp.route("/update-schedule", methods=["POST"])
def update_schedule_job():
    data = request.get_json()
    task_id = data.get("task_id")
    hour = data.get("hour")
    minute = data.get("minute")

    old_task_ref = scheduled_jobs_collection.document(task_id)
    old_task = old_task_ref.get()

    if old_task.exists:
        # Cập nhật nhiệm vụ trong Firebase
        old_task_ref.update(
            {
                "hour": hour,
                "minute": minute,
            }
        )

        # Cập nhật lại nhiệm vụ trong scheduler
        scheduler.reschedule_job(
            task_id,
            trigger=CronTrigger(hour=hour, minute=minute, day="*", month="*", year="*"),
        )

        return jsonify({"message": "Updated successfully!"}), 200
    else:
        return jsonify({"message": "Schedule job is not found!"}), 404


@schedule_job_bp.route("/tasks", methods=["GET"])
def get_tasks():
    scheduled_jobs = scheduled_jobs_collection.get()
    tasks = []
    for job in scheduled_jobs:
        tasks.append(job.to_dict())
    return jsonify({"tasks": tasks}), 200
