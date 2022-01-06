from os import environ
# SQLALCHEMY_DATABASE_URI = "mysql://reactBlog:Ishwar#01@localhost/journal"
SQLALCHEMY_DATABASE_URI = environ["SQLALCHEMY_DATABASE_URI"]
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "sslmode": "allow"
}
SECRET_KEY = environ["SECRET_KEY"]
FRONTEND_SERVER = environ["FRONTEND_SERVER"]
