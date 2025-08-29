from flask import Blueprint, request, jsonify, current_app, url_for
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User
import os
from datetime import datetime
from utils.uploads import save_avatar, allowed_file  # Import utility functions

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        
        # Update user profile
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter(User.email == data['email'], User.id != current_user.id).first()
            if existing_user:
                return jsonify({'success': False, 'message': 'Email already in use'}), 400
            current_user.email = data['email']
        
        if 'first_name' in data:
            current_user.first_name = data['first_name']
            
        if 'last_name' in data:
            current_user.last_name = data['last_name']
            
        if 'bio' in data:
            current_user.bio = data['bio']
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Profile updated successfully',
            'user': {
                'username': current_user.username,
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'bio': current_user.bio
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating profile'}), 500

@profile_bp.route('/api/profile/update-password', methods=['POST'])
@login_required
def update_password():
    try:
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
            
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
            
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
            
        # Update password
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating password: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating password'}), 500

@profile_bp.route('/api/profile/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    try:
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
            
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Save the avatar file
        filename = save_avatar(file, current_user.id)
        
        if not filename:
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
        
        # Update user record with new avatar filename
        current_user.avatar = filename
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Avatar uploaded successfully',
            'avatar_url': url_for('static', filename=f'uploads/avatars/{filename}', _external=True)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading avatar: {str(e)}")
        return jsonify({'success': False, 'message': 'Error uploading avatar'}), 500