from flask import Blueprint, request, jsonify
from database.database import Users, Posts, db, Followers, Messages, SQLAlchemyError
from flask_session import Session
from flask_login import login_required, current_user

api = Blueprint('api', __name__, url_prefix='/api')

session = Session()


@api.route('/')
def home():
    return "HELLO from api!"


@api.route("/user/<username>")
def get_user(username):
    user = Users.get_user_by_username(username)
    if user:
        user = user.json(complete=True)
        posts = Users.query.with_entities(Posts.id).filter_by(author=user["id"], draft=False).all()
        print(posts)
        user["posts"] = [x[0] for x in posts]
        user["followers"] = Followers.get_count(user["id"])
        return jsonify({"resp_code": 200, "response": user})
    return jsonify({"resp_code": 404, "response": "user not found"})


@api.route("/new-story", methods=["POST"])
@login_required
def new_post():
    data: dict = dict(request.get_json())
    status = Posts.new_post(
        title=data["title"],
        subtitle=data["subtitle"],
        content=data["content"],
        author=data["author"],
        thumbnail_image=data["thumbnailURL"],
        tags=data["tags"],
        word_count=data["wordCount"],
        draft=data["draft"]
    )
    return jsonify({"resp_code": 200 if status[0] else 400, "response": status[1]})


@api.route("/posts")
def get_posts():
    posts = [p.json(False) for p in
             Posts.query.filter_by(draft=False).join(Posts.author_rel).order_by(db.desc(Posts.date_published)).all()]
    return jsonify({"resp_code": 200, "response": posts})


@api.route("/search")
def search():
    query = request.args["query"]
    posts = [p.json(False) for p in
             Posts.query.join(Posts.author_rel).filter(
                 Posts.draft.__eq__(False) and (Posts.title.ilike(f"%{query}%") | Posts.tags.ilike(f"%{query}%"))
                 ).order_by(db.desc(Posts.date_published
                                    )).all()]
    return jsonify({"resp_code": 200, "response": posts})


@api.route("/post/<post_id>")
def get_post(post_id):
    post = Posts.get_post(post_id)
    if post:
        if post.draft:
            return jsonify({"resp_code": 401, "response": "Unauthorized access"})
        return jsonify({"resp_code": 200, "response": post.json(True)})
    else:
        return jsonify({"resp_code": 404, "response": "Error: Content not found"})


@api.route("/drafts/<user_id>", methods=["GET"])
@login_required
def get_drafts(user_id):
    posts = Posts.query.filter_by(author=user_id, draft=True).all()
    drafts = []
    print(posts)
    if posts:
        for i in posts:
            drafts.append(i.json())
    return jsonify({"resp_code": 200, "response": drafts})


@api.route("/post/<post_id>/edit", methods=["GET", "POST", "DELETE", "PATCH"])
@login_required
def del_post(post_id):
    post = Posts.get_post(post_id)
    if not post:
        return jsonify({"resp_code": 404, "response": "Not Found"})
    if post.author == current_user.id:
        if request.method == "GET":
            return jsonify({"resp_code": 200, "response": post.json(True)})
        if request.method == "DELETE":
            try:
                db.session.delete(post)
                db.session.commit()
            except SQLAlchemyError or Exception as e:
                print(e)
                return jsonify({"resp_code": 400, "response": e})
            else:
                return jsonify({"resp_code": 200, "response": True})
        if request.method == "POST":
            data = dict(request.get_json())
            data["thumbnail_image"] = data["thumbnailURL"]
            data.pop("thumbnailURL")
            data.pop("author")
            try:
                for key in data.keys():
                    setattr(post, key, data[key])
                db.session.commit()
            except SQLAlchemyError or Exception as e:
                print(e)
                return jsonify({"resp_code": 400, "response": e})
            else:
                return jsonify({"resp_code": 200, "response": True})
        if request.method == "PATCH":
            post.draft = not post.draft
            db.session.commit()
            return jsonify({"resp_code": 200, "response": True})
    return jsonify({"resp_code": 401, "response": "Unauthorized access"})


@api.route("/post/<post_id>/like")
def like_post(post_id):
    post = Posts.query.filter_by(id=int(post_id)).first()
    if post:
        post.increlike()
        return jsonify({"resp_code": 200, "likes": post.likes})

    return jsonify({"resp_code": 400})


@api.route("/follow/<follower_id>", methods=["GET", "POST", "DELETE"])
@login_required
def check_follow(follower_id):
    do_follow = Followers.check_follower(int(follower_id), int(current_user.id))

    if request.method == "POST":
        if not do_follow:
            do_follow = Followers.add_follower(int(follower_id), int(current_user.id))
        return jsonify({"resp_code": 200, "response": bool(do_follow)})

    if request.method == "DELETE":
        if do_follow:
            try:
                db.session.delete(do_follow)
                db.session.commit()
            except SQLAlchemyError as e:
                print(e)
                return jsonify({"resp_code": 200, "response": False})
            else:
                return jsonify({"resp_code": 200, "response": False})
        return jsonify({"resp_code": 200, "response": False})

    return jsonify({"resp_code": 200, "response": bool(do_follow)})


@api.route("/saved", methods=["GET", "POST"])
def saved():
    stories = []
    if "stories" in request.args.keys():
        try:
            ids = list(map(lambda x: int(x), request.args["stories"].split(" ")))
        except Exception as e:
            print(e)
        else:
            try:
                for _id in ids:
                    p = Posts.get_post(_id)
                    if not p.draft:
                        stories.append(p.json())
            except SQLAlchemyError as e:
                print(e)
    return jsonify({"resp_code": 200, "response": stories})


@api.route("/contact", methods=["POST"])
def contact():
    try:
        data = dict(request.get_json())
        query = Messages()
        for key in data:
            setattr(query, key, data[key])
        db.session.add(query)
        db.session.commit()
    except SQLAlchemyError or Exception as e:
        return jsonify({"resp_code": 500, "response": e})
    return jsonify({"resp_code": 200, "response": True})


@api.route("/populars", methods=["GET"])
def get_populars():
    pops = Posts.populars()
    return jsonify({"resp_code": 200, "response": [i.json() for i in pops] if pops else []})
