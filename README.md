# E-commerce App

Flask-based e-commerce REST API with JWT authentication and Chapa payment integration.

## Features

- User authentication (signup/login)
- Product management (CRUD operations)
- Shopping cart functionality
- Chapa payment gateway integration
- SQLite database

## Tech Stack

- Flask 3.1.3
- Flask-JWT-Extended 4.7.4
- Flask-SQLAlchemy 3.1.1
- SQLAlchemy 2.1.6
- Python-dotenv 1.2.4

## Setup

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file with:
   ```
   DATABASE_URL=sqlite:///instance/db.sqlite3
   JWT_SECRET_KEY=your_jwt_secret_key
   CHAPA_SECRET_KEY=your_chapa_secret_key
   CHAPA_URL=https://api.chapa.co/v1/transaction/initialize
   ```

5. Run the application:
   ```bash
   python run.py
   ```

## API Endpoints

### Authentication
- `POST /signup` - Register new user
- `POST /login` - User login (returns JWT token)

### Products (requires authentication)
- `POST /products` - Create product
- `GET /products` - List products (supports pagination and search)
- `GET /products/<id>` - Get product by ID
- `PUT /products/<id>` - Update product

### Cart (requires authentication)
- `POST /cart` - Add product to cart
- `GET /cart` - View cart items
- `PUT /cart/<id>` - Update cart item quantity
- `DELETE /cart/<id>` - Remove item from cart

### Checkout (requires authentication)
- `POST /checkout` - Initialize payment (supports ETB and USD)

## Database Models

- **Users**: id, username, email, password, created_at
- **Products**: id, name, description, price, stock_quantity, created_at, updated_at
- **CartItems**: id, user_id, product_id, quantity, created_at
- **Payments**: id, user_id, tx_ref, amount, currency, status, created_at

## Authentication

All endpoints except `/signup` and `/login` require JWT token in Authorization header:
```
Authorization: Bearer <token>
```
