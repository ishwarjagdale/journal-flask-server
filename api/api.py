from flask import Blueprint, request, jsonify
from database.database import Users, Posts, db
from flask_session import Session

api = Blueprint('api', __name__, url_prefix='/api')

session = Session()


@api.route('/')
def home():
    return "HELLO from api!"


@api.route("/user/<username>")
def get_user(username):
    user = Users.get_user_by_username(username).json()
    posts = Users.query.with_entities(Posts.id).filter_by(author=user["id"]).all()
    print(posts)
    user["posts"] = [x[0] for x in posts]
    return jsonify({"resp_code": 200, "response": user})


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


@api.route("/post/<post_id>/like")
def like_post(post_id):
    post = Posts.query.filter_by(id=int(post_id)).first()
    if post:
        post.increlike()
        return jsonify({"resp_code": 200, "likes": post.likes})

    return jsonify({"resp_code": 400})
