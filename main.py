from flask_cors import CORS
from auth_controller import auth_bp
from ESP_controller import esp8266_bp
from deep_face_model import preload_model
from schedule_job_controller import (
    app,
    schedule_job_bp,
)

CORS(app)
app.register_blueprint(auth_bp)
app.register_blueprint(esp8266_bp)
app.register_blueprint(schedule_job_bp)


if __name__ == "__main__":
    preload_model()
    app.run(debug=True, port=9999)
