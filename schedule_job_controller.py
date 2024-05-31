from flask import Blueprint, Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask_sqlalchemy import SQLAlchemy
import atexit, requests

app = Flask(__name__)

# Cấu hình SQLAlchemy cho SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
db = SQLAlchemy(app)

schedule_job_bp = Blueprint("schedule_job", __name__)


# Định nghĩa model Task để lưu thông tin nhiệm vụ
class Task(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    action = db.Column(db.String(120), nullable=False)
    hour = db.Column(db.Integer, nullable=False)  # Giờ cần chạy nhiệm vụ
    minute = db.Column(db.Integer, nullable=False)  # Phút cần chạy nhiệm vụ


# Khởi tạo BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Đảm bảo scheduler dừng khi ứng dụng Flask dừng
atexit.register(lambda: scheduler.shutdown())

# Load các tasks đã lưu trong DB mỗi khi run lại server
is_loaded_stored_tasks = False


def load_tasks():
    with app.app_context():
        global is_loaded_stored_tasks
        if is_loaded_stored_tasks:
            return
        tasks = Task.query.all()
        for task in tasks:
            scheduler.add_job(
                func=scheduled_task,
                trigger=CronTrigger(
                    hour=task.hour, minute=task.minute, day="*", month="*", year="*"
                ),
                args=[task.id],
                id=task.id,
            )
        is_loaded_stored_tasks = True


# Hàm nhiệm vụ bạn muốn chạy theo lịch
def scheduled_task(task_id):
    with app.app_context():
        task = Task.query.get(task_id)
        if task:
            print("Running task", task.action)
            base_url = (
                "http://localhost:9999"  # Đảm bảo sử dụng URL của server Flask của bạn
            )

            if task.action == "turn on led home":
                url = f"{base_url}/led?location=living-room&status=1"
            elif task.action == "turn on led garden":
                url = f"{base_url}/led?location=garden&intensity=255"
            elif task.action == "turn on fan":
                url = f"{base_url}/fan?location=living-room&status=1"
            else:
                print(f"Unknown task action: {task.action}")
                return

            # Gửi yêu cầu HTTP
            response = requests.get(url)
            print(f"Requested {url}, response status code: {response.status_code}")


# Tạo bảng trong cơ sở dữ liệu và load tasks khi khởi động
with app.app_context():
    db.create_all()
    load_tasks()


@schedule_job_bp.route("/schedule", methods=["POST"])
def schedule_task():
    data = request.get_json()
    user_id = data.get("user_id")
    action = data.get("action")
    hour = data.get("hour")
    minute = data.get("minute")

    # Lưu nhiệm vụ vào cơ sở dữ liệu
    task_id = f"{user_id}->{action}"
    new_task = Task(id=task_id, hour=hour, minute=minute, action=action)
    db.session.add(new_task)
    db.session.commit()

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
    user_id = data.get("user_id")
    action = data.get("action")
    hour = data.get("hour")
    minute = data.get("minute")

    task_id = f"{user_id}->{action}"
    task = Task.query.get(task_id)
    if task:
        task.action = action
        task.hour = hour
        task.minute = minute
        db.session.commit()

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
    tasks = Task.query.all()
    task_list = []
    for task in tasks:
        task_list.append(
            {
                "id": task.id,
                "action": task.action,
                "hour": task.hour,
                "minute": task.minute,
            }
        )
    return jsonify({"tasks": task_list}), 200
