# verify_admin.py
from app import app, db
from models import User

with app.app_context():
    user = User.query.get(1)
    print(f"User: {user.username}")
    print(f"Is admin: {user.is_admin}")
    print(f"Is active: {user.is_active}")