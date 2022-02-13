import os
from PIL import Image
import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from google.cloud import storage
from google.cloud.storage import Bucket
from google.oauth2.service_account import Credentials
from database.database import Users

statics = Blueprint("storage", __name__, url_prefix="/static")


@statics.route("/", methods=["GET", "POST"])
@login_required
def upload_file():
    try:
        file = request.files["upload"]
        print(file.content_type)
        if "fileCat" in request.form.keys() and request.form["fileCat"] == "profileImage":
            filename = request.form.get("fileCat") + ".webp"
        else:
            filename = str(datetime.datetime.utcnow()) + '_' + file.filename[:file.filename.rfind('.') + 1] + 'webp'

        Image.open(file).save(filename, format="webp")
        storage_client = storage.Client(credentials=Credentials.from_service_account_file(
            os.path.join(os.path.dirname(__file__), os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        ))
        bucket = Bucket.from_string(os.environ["BUCKET"], client=storage_client)
        if "fileCat" in request.form.keys() and request.form["fileCat"] == "profileImage":
            blob = bucket.blob(f"uploads/{str(current_user.id)}/user/{filename}")
        else:
            blob = bucket.blob(f"uploads/{str(current_user.id)}/{filename}")

        blob.upload_from_filename(filename, content_type="image/webp")
        blob.make_public()
        print(blob, blob.public_url)
        if "fileCat" in request.form.keys():
            match request.form.get("fileCat"):
                case "profileImage":
                    Users.update(current_user.id, {
                        "key": ["image_url", blob.public_url]
                    })
        os.remove(filename)
    except KeyError or BaseException or Exception as e:
        return jsonify(False)

    return jsonify({"url": blob.public_url})
