from app import app, db
from models import User, ProcessedImage

with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    
    print("All users in database:")
    users = User.query.all()
    
    if not users:
        print("No users found in the database.")
        print("Please register a user first through your application.")
    else:
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
        
        user_id = input("\nEnter the user ID to make admin: ")
        
        try:
            user = User.query.get(int(user_id))
            if user:
                user.is_admin = True
                db.session.commit()
                print(f"Success! {user.username} is now an admin.")
            else:
                print("User not found!")
        except ValueError:
            print("Please enter a valid number.")