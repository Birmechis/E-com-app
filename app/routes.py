from flask import jsonify, request, Blueprint
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
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

    token = create_access_token(identity=str(user.id))

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

    if name is None or description is None or price is None or stock_quantity is None:
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
        "created_at": new_products.created_at.isoformat() if new_products.created_at else None,
    }), 201

@bp.route('/products', methods=['GET'])
@jwt_required()
def get_products():

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search_name = request.args.get('search', type=str)

    query = Products.query

    if search_name:
        query = query.filter(Products.name.ilike(f"%{search_name}%"))

    calculate_offset = (page - 1) * limit
    total_count = query.count()
    records = query.offset(calculate_offset).limit(limit).all()

    return jsonify({
        "products": [
            {
                "id": prod.id,
                "name": prod.name,
                "description": prod.description,
                "price": prod.price,
                "stock_quantity": prod.stock_quantity,
                "created_at": prod.created_at.isoformat() if prod.created_at else None,
            }for prod in records
        ],
        "page": page,
        "limit": limit,
        "total": total_count,
    }), 200

@bp.route('/products/<int:id>', methods=['GET'])
@jwt_required()
def get_products_by_id(id):

    product = Products.query.get(id)
    if not product:
        return jsonify({
            "error": "Product does not exist"
        }), 404

    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock_quantity": product.stock_quantity,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }), 200

@bp.route('/products/<int:id>', methods=['PUT'])
@jwt_required()
def update_products(id):

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid or missing json payload"
        }), 400

    product = Products.query.get_or_404(id)

    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    stock_quantity = data.get("stock_quantity")

    if name is None or description is None or price is None or stock_quantity is None:
        return jsonify({
            "error": "Missing required fields"
        }), 400

    try:
        price = float(price)
        stock_quantity = int(stock_quantity)
        if price < 0.0 or stock_quantity < 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "error": "Price must be number and stock quantity must be integer"
        }), 400

    product.name = name
    product.description = description
    product.price = price
    product.stock_quantity = stock_quantity

    db.session.commit()
    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock_quantity": product.stock_quantity,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }), 200

@bp.route('/cart',methods=['POST'])
@jwt_required()
def add_products_to_cart():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid or missing JSON payload"
        }), 400

    product_id = data.get("product_id")
    quantity = data.get("quantity")
    user_id = get_jwt_identity()

    product = Products.query.get(product_id)
    if not product:
        return jsonify({
            "error": "Product does not exist"
        }), 404

    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "error": "Quantity must be positive integer"
        }), 400

    if product.stock_quantity < quantity:
        return jsonify({
            "error": f"Only {product.stock_quantity} items left in stock"
        }), 400

    existing_cart_items = CartItems.query.filter_by(user_id=user_id, product_id=product_id).first()
    if existing_cart_items:
        if product.stock_quantity < (existing_cart_items.quantity + quantity):
            return jsonify({
                "error": "Cannot add more. Exceeds available stock"
            }), 400

        existing_cart_items.quantity += quantity
    else:
        new_cart_item = CartItems(
            user_id = user_id,
            product_id = product_id,
            quantity = quantity,
        )
        db.session.add(new_cart_item)

    db.session.commit()

    return jsonify({
        "message": f"Successfully added {product.name} to cart"
    }), 200

@bp.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():

    user_id = get_jwt_identity()

    cart = CartItems.query.filter_by(user_id=user_id).all()
    if not cart:
        return jsonify({
            "error": "CartItem does not exist"
        }), 404

    result = []
    for item in cart:
        result.append({
            "id": item.id,
            "quantity": item.quantity,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })

    return jsonify({
        "cart": result
    }), 200
