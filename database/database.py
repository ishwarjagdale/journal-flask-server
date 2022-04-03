import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_login import UserMixin

db = SQLAlchemy()


def username_default(context):
    username = context.get_current_parameters()["email"].split("@")[0]
    if Users.query.filter_by(username=username).first():
        return username + "_" + str(context.get_current_parameters()["id"])
    return username


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False,
                         default=username_default)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    bio = db.Column(db.String(200))
    image_url = db.Column(db.String(500), default="https://storage.googleapis.com/dotted-tube-339407.appspot.com"
                                                  "/assets/img/user.png")
    bg_image_url = db.Column(db.String(500), default="https://storage.googleapis.com/dotted-tube-339407.appspot.com"
                                                     "/assets/img/user.png")
    is_authenticated = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)

    def json(self, complete=False):
        user = {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "bio": self.bio,
            "email": self.email,
            "image_url": self.image_url
        }

        if complete:
            user["bg_image_url"] = self.bg_image_url

        return user

    @staticmethod
    def register(name, email, password):
        if Users.query.filter_by(email=email).first():
            return False, "user exist"

        try:
            user = Users(name=name, email=email, password=password)
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError as e:
            print(e)
            print(e.code)
            return False, e.code
        else:
            user = Users.query.filter_by(email=email).first()
            return True, user

    @staticmethod
    def get(user_id):
        return Users.query.filter_by(id=user_id).first()

    @staticmethod
    def get_user_by_username(username):
        return Users.query.filter_by(username=username).first()

    @staticmethod
    def update(user_id: int, settings: dict):
        user = Users.query.filter_by(id=user_id).first()
        for key in settings.keys():
            print(key, settings[key])
            setattr(user, key, settings[key])
        print(user.json(complete=True))
        db.session.commit()
        return Users.get(user_id)

    def get_follow_count(self):
        count = Followers.query.filter_by(author=self.id).all().count()
        print(count)
        return count


def default_date_modified(context):
    return context.get_current_parameters()["date_published"]


def default_character_count(context):
    return len(context.get_current_parameters()["content"])


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000), nullable=False)
    subtitle = db.Column(db.String(1000), nullable=False)
    content = db.Column(db.String(10000), nullable=False)
    author = db.Column(db.Integer, db.ForeignKey("users.id"))

    author_rel = db.relationship("Users", foreign_keys=[author])

    thumbnail_image = db.Column(db.String(1000), nullable=True,
                                default="https://storage.googleapis.com/dotted-tube-339407.appspot.com/assets/img"
                                        "/thumbnail.png")
    date_published = db.Column(db.DateTime, nullable=False)
    date_modified = db.Column(db.DateTime, default=default_date_modified,
                              nullable=False, onupdate=datetime.datetime.now())
    tags = db.Column(db.String(1000), nullable=True)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    character_count = db.Column(db.Integer, default=default_character_count)
    word_count = db.Column(db.Integer, default=0)
    draft = db.Column(db.Boolean, default=False)

    def json(self, complete=False):
        post = {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "author": {
                "id": self.author_rel.id,
                "url": f"/@{self.author_rel.username}",
                "name": self.author_rel.name,
                "img": self.author_rel.image_url
            },
            "meta": {
                "date_published": self.date_published,
                "read_time": self.word_count,
                "tag": self.tags,
                "likes": self.likes,
                "response": self.views,
                "draft": self.draft
            },
            "thumbnail": {
                "url": self.thumbnail_image,
                "caption": self.title,
            },
            "url": f"/s/{self.title.replace(' ', '-')}-{self.id}"
        }
        if complete:
            post["content"] = self.content
        return post

    @staticmethod
    def get_post(post_id, every=False):
        if every:
            post = Posts.query.filter_by(id=post_id).first()
        else:
            post = Posts.query.filter_by(id=post_id, draft=False).first()
        if post:
            post.views += 1
            db.session.commit()
            return post
        return False

    def view(self):
        self.views += 1
        db.session.commit()

    def increlike(self):
        self.likes += 1
        db.session.commit()

    @staticmethod
    def new_post(title, subtitle, content, author, thumbnail_image, tags, word_count):
        try:
            post = Posts(title=title, subtitle=subtitle, author=author, content=content,
                         thumbnail_image=thumbnail_image, tags=tags, word_count=word_count,
                         date_published=datetime.datetime.now(),
                         date_modified=datetime.datetime.now())
            db.session.add(post)
            db.session.commit()
        except SQLAlchemyError as e:
            print(e)
            print(e.code)
            db.session.rollback()
            return False, e.code
        else:
            return True, post.id

    @staticmethod
    def update_post(post_id: int, post_changes: dict):
        try:
            post = Posts.query.filter_by(id=post_id).first()
            for key in post_changes.keys():
                setattr(post, key, post_changes[key])
            db.session.commit()

        except SQLAlchemyError as e:
            return False, e.code
        else:
            return True


class Followers(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    author_rel = db.relationship("Users", foreign_keys=[author])
    follower_rel = db.relationship("Users", foreign_keys=[follower_id])

    @staticmethod
    def get_count(user_id):
        count = db.session.query(db.func.count(Followers.author)).filter_by(author=user_id).first()
        print(count)
        return count[0]

    @staticmethod
    def add_follower(user_id, follower_id):
        try:
            follow = Followers(author=user_id, follower_id=follower_id)
            db.session.add(follow)
            db.session.commit()
        except SQLAlchemyError as e:
            print(e)
            return False
        else:
            return True

    @staticmethod
    def check_follower(profile_id, follower_id):
        try:
            do_follow = Followers.query.filter_by(author=profile_id, follower_id=follower_id).first()
            print(do_follow)
        except SQLAlchemyError as e:
            print(e)
            return None
        else:
            return do_follow
