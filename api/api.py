from flask import Blueprint, request, jsonify
from database.database import Users, Posts, db
from flask_login import login_required, current_user

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/')
def home():
    return "HELLO from api!"


@api.route("/user/<username>", methods=["GET", "POST"])
def get_user(username):
    return jsonify({"resp_code": 200, "response": Users.get_user_by_username(username).json()})


@api.route("/settings", methods=["GET", "POST"])
@login_required
def setting():
    if request.method == "POST":
        data = dict(request.get_json())
        print(data)
        Users.update(current_user.id, data)

        return jsonify(True)
    return jsonify({"resp_code": 200, "response": "userSettings", "settings": current_user.json()})


@api.route("/new-story", methods=["POST"])
def new_post():
    data: dict = dict(request.get_json())
    status = Posts.new_post(
                            title=data["title"],
                            subtitle=data["subtitle"],
                            content=data["content"],
                            author=data["author"],
                            thumbnail_image=data["thumbnailURL"],
                            tags=data["tags"]
                            )
    return jsonify({"resp_code": 200 if status[0] else 400, "response": status[1]})


@api.route("/posts")
def get_posts():
    posts = [p.json(False) for p in Posts.query.join(Posts.author_rel).order_by(db.desc(Posts.date_published)).all()]
    print(*posts, sep="\n")
    return jsonify({"resp_code": 200, "response": posts})


@api.route("/post/<post_id>")
def get_post(post_id):
    post = Posts.get_post(post_id).json(True)
    if post:
        return jsonify({"resp_code": 200, "response": post})
    else:
        return jsonify({"resp_code": 404, "response": "noPostFound"})
