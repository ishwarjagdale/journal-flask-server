from flask import Flask
from database.database import db
from api.api import api
from auth.auth import login_manager
from flask_cors import CORS
from auth.auth import toAuth
from os import environ
from api.api import session
from Storage.storage import statics

app = Flask(__name__)
cors = CORS(origins=environ["FRONTEND_SERVER"], supports_credentials=True)
app.secret_key = environ["SECRET_KEY"]
app.config["SESSION_TYPE"] = "filesystem"

with app.app_context():
    app.config.from_pyfile("config.py")
    login_manager.init_app(app)
    cors.init_app(app)
    session.init_app(app)
    db.init_app(app)
    db.create_all()

    app.register_blueprint(api)
    app.register_blueprint(toAuth)
    app.register_blueprint(statics)

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
