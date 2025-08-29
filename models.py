from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(120), default='default-avatar.png')  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class ProcessedImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    processed_filename = db.Column(db.String(255), nullable=False)
    process_type = db.Column(db.String(50), nullable=False)  # 'detection' or 'removal'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('processed_images', lazy=True))
    
    def delete_files(self, app):
        """Delete the associated files from the filesystem"""
        import os
        from flask import current_app
        
        # Get the app instance if not provided
        if app is None:
            app = current_app
        
        # Delete the processed file
        processed_path = os.path.join(app.config['RESULTS_FOLDER'], self.processed_filename)
        if os.path.exists(processed_path):
            os.remove(processed_path)
        
        file_id = self.processed_filename.split('_')[0]
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_original.jpg")
        if os.path.exists(original_path):
            os.remove(original_path)
    
    def get_image_url(self):
        """Get the URL to access the processed image"""
        from flask import url_for
        return url_for('static', filename='results/' + self.processed_filename)