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
    image_url = db.Column(db.String(500), default="/img/user.png")
    is_authenticated = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)

    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "bio": self.bio,
            "email": self.email,
            "image_url": self.image_url
        }

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
            setattr(user, settings[key][0], settings[key][1])
        print(user.json())
        db.session.commit()
        return Users.get(user_id)


def default_date_modified(context):
    return context.get_current_parameters()["date_published"]


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000), nullable=False)
    subtitle = db.Column(db.String(1000), nullable=False)
    content = db.Column(db.String(10000), nullable=False)
    author = db.Column(db.Integer, db.ForeignKey("users.id"))

    author_rel = db.relationship("Users", foreign_keys=[author])

    thumbnail_image = db.Column(db.String(1000), nullable=True,
                                default="/img/thumbnail.png")
    date_published = db.Column(db.DateTime, nullable=False)
    date_modified = db.Column(db.DateTime, default=default_date_modified,
                              nullable=False, onupdate=datetime.datetime.now())
    tags = db.Column(db.String(1000), nullable=True)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)

    def json(self, complete):
        post = {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "author": {
                "url": f"/@{self.author_rel.username}",
                "name": self.author_rel.name,
                "img": self.author_rel.image_url
            },
            "meta": {
                "date_published": self.date_published,
                "read_time": "4 min read",
                "tag": self.tags,
                "likes": self.likes,
                "response": self.views
            },
            "thumbnail": {
                "url": self.thumbnail_image,
                "caption": self.title,
            },
            "url": f"/s/{self.title.replace(' ',  '-')}-{self.id}"
        }
        if complete:
            post["content"] = self.content
        return post

    @staticmethod
    def get_post(post_id):
        post = Posts.query.filter_by(id=post_id).first()
        post.views += 1
        db.session.commit()
        return post if post is not None else False

    def view(self):
        self.views += 1
        db.session.commit()

    def increlike(self):
        self.likes += 1
        db.session.commit()

    @staticmethod
    def new_post(title, subtitle, content, author, thumbnail_image, tags):
        try:
            post = Posts(title=title, subtitle=subtitle, author=author, content=content,
                         thumbnail_image=thumbnail_image, tags=tags, date_published=datetime.datetime.now(),
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
