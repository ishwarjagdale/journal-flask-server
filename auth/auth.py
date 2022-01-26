from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database.database import Users
from flask import Blueprint, request, jsonify

toAuth = Blueprint('auth', __name__, url_prefix='/auth')

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return Users.get(user_id)


@toAuth.route("/", methods=["POST"])
def register_user():
    try:
        data = dict(request.get_json())
        print(f"New user: {data['name']} ({data['email']}) registering...", end="")
        user = Users.register(data["name"], data["email"], data["password"])
        print("registered...", end="")
        if user[0]:
            print("OK")
            return jsonify({"resp_code": 200, "response": "userRegistered", "user": user.json()})
        else:
            print("userExists")
            return jsonify({"resp_code": 500, "response": "userExists"})
    except Exception:
        return jsonify({"resp_code": 500, "response": "Server Error"})


@toAuth.route("/login", methods=["POST"])
def login():
    credentials = request.form.to_dict() or dict(request.get_json())
    remember = credentials["rememberMe"] if credentials.__contains__("rememberMe") else False
    if credentials.__contains__("email") and credentials.__contains__("password"):
        user = Users.query.filter_by(email=credentials["email"]).first()
        if user:
            print(f"{user.email}({user.id})({remember}) logging in...", end="")
            if credentials["password"] == user.password:
                login_user(user, remember=True if remember == "on" else False)
                print("OK")
                return jsonify({"resp_code": 200, "response": "userLoggedIn", "user": user.json()})
            else:
                print("Failed(Wrong Credentials)")
                return jsonify({"resp_code": 404, "response": "wrong credentials"})
        else:
            print(f"User: {credentials['email']} doesn't exist!")
            return jsonify({"resp_code": 404, "response": "userNotFound"})
    return jsonify({"resp_code": 404, "response": "Invalid request, missing credentials"})


@toAuth.route("/logout")
@login_required
def logout():
    print(f"{current_user.email}({current_user.id}) logging out...", end="")
    logout_user()
    print("OK")
    return jsonify({"resp_code": 200, "response": "userLoggedOut"})


@toAuth.route("/secure", methods=["GET", "POST"])
@login_required
def secure():
    if request.method == "POST":
        if dict(request.get_json())["userId"] == current_user.id:
            return jsonify({"resp_code": 200})
        else:
            return jsonify({"resp_code": 400})
    print("accessed")
    return jsonify({"resp_code": 200, "response": current_user.json()})


@toAuth.route("/settings", methods=["GET", "POST"])
@login_required
def setting():
    print(current_user.email)
    if request.method == "POST":
        data = dict(request.get_json())
        print(data)
        Users.update(current_user.id, data)

        return jsonify(True)
    return jsonify({"resp_code": 200, "response": "userSettings", "settings": current_user.json()})
