from flask import Flask
from database.database import db
from api.api import api
from auth.auth import login_manager
from flask_cors import CORS
from auth.auth import toAuth


app = Flask(__name__)

with app.app_context():
    app.config.from_pyfile("config.py")
    app.register_blueprint(api)
    app.register_blueprint(toAuth)
    login_manager.init_app(app)
    cors = CORS(origins=app.config["FRONTEND_SERVER"], supports_credentials=True)
    cors.init_app(app)
    db.init_app(app)
    db.create_all()


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
