from flask import jsonify, request, Blueprint
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import Users, Products, CartItems
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

    hashed_password = generate_password_hash(password)

    new_user = Users(
        username = username,
        email = email,
        password = hashed_password,
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Username or email already exists"
        }), 409

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

@bp.route('/products', methods=['POST'])
@jwt_required()
def create_products():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid or missing json payload"
        }), 400

    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    stock_quantity = data.get("stock_quantity")

    if not name or not description or not price or not stock_quantity:
        return jsonify({
            "error": "Missing name or description or price or stock_quantity"
        }), 400

    existing_products = Products.query.filter_by(name=name).first()
    if existing_products:
        return jsonify({
            "error": "Product already exists"
        }), 409

    try:
        price = float(price)
        stock_quantity = int(stock_quantity)
        if price < 0.0 or stock_quantity < 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "error": "Price must be number and stock quantity must be integer"
        }), 400

    new_products = Products(
        name = name,
        description = description,
        price = price,
        stock_quantity = stock_quantity,
    )

    try:
        db.session.add(new_products)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "An unexpected error occurred while saving to the database."
        }), 500

    return jsonify({
        "name": new_products.name,
        "description": new_products.description,
        "price": new_products.price,
        "stock_quantity": new_products.stock_quantity,
        "created_at": new_products.created_at,
    }), 201

@bp.route('/products/<int:id>',methods=['POST'])
@jwt_required()
def add_products_to_cart(id):
    data = request.get_json(silent=True)

    product_id = data.get("product_id")
    quantity = data.get("quantity")

    product = Products.query.get(product_id)
    if not product:
        return jsonify({
            "error": "Product does not exist"
        }), 404

    if product.stock_quantity < quantity:
        return jsonify({
            "error": f"Only {product.stock_quantity} items left in stock"
        }), 400

    existing_cart_items = CartItems.query.filter_by(product_id=product_id).first()
    if existing_cart_items:
        if product.stock_quantity < (existing_cart_items.quantity + quantity):
            return jsonify({
                "error": "Cannot add more. Exceeds available stock"
            }), 400

        existing_cart_items.quantity += quantity
    else:
        new_cart_item = CartItems(
            product_id = product_id,
            quantity = quantity,
        )
        db.session.add(new_cart_item)

    db.session.commit()

    return jsonify({
        "message": f"Successfully added {product.name} to cart"
    }), 200

