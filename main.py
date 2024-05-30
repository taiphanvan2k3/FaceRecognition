from flask import Flask
from flask_cors import CORS
from auth_controller import auth_bp
from deep_face_model import preload_model

app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    preload_model()
    app.run(debug=True, port=9999)
