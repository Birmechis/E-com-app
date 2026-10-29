from flask import jsonify, request, Blueprint
from flask_jwt_extended import jwt_required, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import Users
from app import db

bp = Blueprint('api', __name__)

@bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid or missing json payload"
        }), 400

    username = data.get("username", '').strip()
    email = data.get("email", '').strip()
    password = data.get("password", '')

    if not username or not email or not password:
        return jsonify({
            "error": "Missing username or email or password"
        }), 400

    existing_user = Users.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({
            "error": "User already exists"
        }), 409

    hashed_password = generate_password_hash(password)

    new_user = Users(
        username = username,
        email = email,
        password = hashed_password,
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "username": new_user.username,
        "email": new_user.email,
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid or missing json payload"
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "error": "Missing email or password"
        }),400

    user = Users.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not check_password_hash(user.password, password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    token = create_access_token(identity=user.id)

    return jsonify({
        "message": "login successful",
        "token": token
    }), 200


