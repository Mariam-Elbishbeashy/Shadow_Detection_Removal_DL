from flask import Flask, request, send_file, render_template, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import cv2
import numpy as np
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from routes import profile_bp
import os, requests

# Import models and functions
from models import db, User, ProcessedImage
from shadow_detection import build_model, overlay_mask_on_image, dice_coefficient, iou_score
from shadow_removal import remove_shadow
from admin_route import (
    admin_dashboard, admin_users, admin_user_detail, admin_activity,
    admin_delete_image, admin_delete_user, admin_toggle_user_status,
    admin_make_admin, admin_remove_admin, admin_system_stats, admin_view_image
)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shadow_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = os.path.join('static', 'results')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'avatars')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 
app.register_blueprint(profile_bp)

# Register admin routes
app.add_url_rule('/admin', 'admin_dashboard', admin_dashboard)
app.add_url_rule('/admin/users', 'admin_users', admin_users)
app.add_url_rule('/admin/user/<int:user_id>', 'admin_user_detail', admin_user_detail)
app.add_url_rule('/admin/activity', 'admin_activity', admin_activity)
app.add_url_rule('/admin/delete_image/<int:image_id>', 'admin_delete_image', admin_delete_image, methods=['POST'])
app.add_url_rule('/admin/delete_user/<int:user_id>', 'admin_delete_user', admin_delete_user, methods=['POST'])
app.add_url_rule('/admin/toggle_user/<int:user_id>', 'admin_toggle_user_status', admin_toggle_user_status, methods=['POST'])
app.add_url_rule('/admin/make_admin/<int:user_id>', 'admin_make_admin', admin_make_admin, methods=['POST'])
app.add_url_rule('/admin/remove_admin/<int:user_id>', 'admin_remove_admin', admin_remove_admin, methods=['POST'])
app.add_url_rule('/admin/make_admin/<int:user_id>', 'admin_make_admin', admin_make_admin, methods=['POST'])
app.add_url_rule('/admin/remove_admin/<int:user_id>', 'admin_remove_admin', admin_remove_admin, methods=['POST'])
app.add_url_rule('/admin/stats', 'admin_system_stats', admin_system_stats)
app.add_url_rule('/admin_view_image/<int:image_id>', 'admin_view_image', admin_view_image)

# Force CPU (avoid CUDA errors)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1" 
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

MODEL_PATH = "utils/shadow_model2_0850_K2S2E5_aug.h5"
MODEL_URL = "https://drive.google.com/uc?id=1TQYO8QbcG2HfD3uuRc0gfefDJo4HjWv6&export=download"

# Download model if not exists
if not os.path.exists(MODEL_PATH):
    print("Downloading model from Google Drive...")
    os.makedirs("utils", exist_ok=True)
    r = requests.get(MODEL_URL, allow_redirects=True)
    with open(MODEL_PATH, "wb") as f:
        f.write(r.content)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Global variable to store the model
model = None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================== AUTHENTICATION ROUTES ==================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.errorhandler(403)
def access_denied(error):
    return render_template('access_denied.html'), 403

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('signup.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully. Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ================== APPLICATION ROUTES ==================

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

@app.route('/api/docs')
def api_docs():
    """Return JSON API documentation"""
    docs = {
        "api_endpoints": {
            "auth": {
                "login": {"method": "POST", "endpoint": "/login", "description": "User authentication"},
                "signup": {"method": "POST", "endpoint": "/signup", "description": "User registration"},
                "logout": {"method": "GET", "endpoint": "/logout", "description": "User logout"}
            },
            "processing": {
                "detect": {"method": "POST", "endpoint": "/detect", "description": "Detect shadows in image"},
                "remove": {"method": "POST", "endpoint": "/remove", "description": "Remove shadows from image"}
            },
            "images": {
                "history": {"method": "GET", "endpoint": "/history", "description": "Get processing history"},
                "view": {"method": "GET", "endpoint": "/view_image/<int:image_id>", "description": "View processed image"},
                "download": {"method": "GET", "endpoint": "/download_image/<int:image_id>", "description": "Download processed image"},
                "delete": {"method": "POST", "endpoint": "/delete_image/<int:image_id>", "description": "Delete processed image"}
            }
        },
        "request_examples": {
            "detect": {
                "method": "POST",
                "endpoint": "/detect",
                "content_type": "multipart/form-data",
                "parameters": {
                    "image": "File upload (required)"
                }
            }
        },
        "response_examples": {
            "success": {
                "detect": {
                    "status": "success",
                    "message": "Image processed successfully",
                    "image_url": "/view_image/123"
                }
            },
            "error": {
                "detect": {
                    "status": "error",
                    "message": "No image provided"
                }
            }
        }
    }
    return jsonify(docs)

@app.route('/detect', methods=['POST'])
@login_required
def detect():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_original.jpg")
    result_path = os.path.join(app.config['RESULTS_FOLDER'], f"{file_id}_detection.jpg")
    
    # Save the uploaded file
    file.save(upload_path)
    
    try:
        # Detect shadows
        overlay, mask = detect_shadows_web(upload_path)
        
        # Save the result
        cv2.imwrite(result_path, overlay)
        
        # Save to database
        processed_image = ProcessedImage(
            user_id=current_user.id,
            original_filename=file.filename,
            processed_filename=f"{file_id}_detection.jpg",
            process_type='detection'
        )
        db.session.add(processed_image)
        db.session.commit()
        
        # Return the processed image
        return send_file(result_path, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({'error': f'Detection failed: {str(e)}'}), 500

@app.route('/remove', methods=['POST'])
@login_required
def remove():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_original.jpg")
    result_path = os.path.join(app.config['RESULTS_FOLDER'], f"{file_id}_removal.jpg")
    
    # Save the uploaded file
    file.save(upload_path)
    
    try:
        # First detect shadows to get the mask
        _, mask = detect_shadows_web(upload_path)
        
        # Remove shadows using the mask
        result = remove_shadows_web(upload_path, mask)
        
        # Save the result
        cv2.imwrite(result_path, result)
        
        # Save to database
        processed_image = ProcessedImage(
            user_id=current_user.id,
            original_filename=file.filename,
            processed_filename=f"{file_id}_removal.jpg",
            process_type='removal'
        )
        db.session.add(processed_image)
        db.session.commit()
        
        # Return the processed image
        return send_file(result_path, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({'error': f'Removal failed: {str(e)}'}), 500

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
    
@app.route('/history')
@login_required
def history():
    processed_images = ProcessedImage.query.filter_by(user_id=current_user.id).order_by(ProcessedImage.created_at.desc()).all()
    return render_template('history.html', images=processed_images)

@app.route('/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    # Find the image
    processed_image = ProcessedImage.query.get_or_404(image_id)
    
    # Check if the user owns this image
    if processed_image.user_id != current_user.id:
        flash('You do not have permission to delete this image', 'danger')
        return redirect(url_for('history'))
    
    try:
        # Delete the associated files
        processed_image.delete_files(app)
        
        # Delete from database
        db.session.delete(processed_image)
        db.session.commit()
        
        flash('Image deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting image: {str(e)}', 'danger')
    
    return redirect(url_for('history'))

# app.py - Add this route
@app.route('/view_image/<int:image_id>')
@login_required
def view_image(image_id):
    # Find the image
    processed_image = ProcessedImage.query.get_or_404(image_id)
    
    # Check if the user owns this image
    if processed_image.user_id != current_user.id:
        flash('You do not have permission to view this image', 'danger')
        return redirect(url_for('history'))
    
    # Check if the file exists
    image_path = os.path.join(app.config['RESULTS_FOLDER'], processed_image.processed_filename)
    if not os.path.exists(image_path):
        flash('Image file not found', 'danger')
        return redirect(url_for('history'))
    
    # Return the image
    return send_file(image_path, mimetype='image/jpeg')

# app.py - Add this route for downloading images
@app.route('/download_image/<int:image_id>')
@login_required
def download_image(image_id):
    # Find the image
    processed_image = ProcessedImage.query.get_or_404(image_id)
    
    # Check if the user owns this image
    if processed_image.user_id != current_user.id:
        flash('You do not have permission to download this image', 'danger')
        return redirect(url_for('history'))
    
    # Check if the file exists
    image_path = os.path.join(app.config['RESULTS_FOLDER'], processed_image.processed_filename)
    if not os.path.exists(image_path):
        flash('Image file not found', 'danger')
        return redirect(url_for('history'))
    
    # Return the image as an attachment for download
    return send_file(
        image_path, 
        mimetype='image/jpeg',
        as_attachment=True,
        download_name=f"{processed_image.process_type}_{processed_image.original_filename}"
    )

# ================== HELPER FUNCTIONS ==================

def load_shadow_model():
    global model
    if model is None:
        try:
            # Try to load the pre-trained model
            import tensorflow as tf
            model_path = 'utils/shadow_model2_0850_K2S2E5_aug.h5'
            if os.path.exists(model_path):
                model = tf.keras.models.load_model(
                    model_path,
                    custom_objects={
                        'dice_coefficient': dice_coefficient,
                        'iou_score': iou_score
                    }
                )
                print("Model loaded successfully")
            else:
                # Build a new model if pre-trained doesn't exist
                print("Pre-trained model not found, building new model...")
                model = build_model()
        except Exception as e:
            print(f"Error loading model: {e}")
            model = build_model()
    return model

def detect_shadows_web(image_path):
    # Load the model
    model = load_shadow_model()

    # Read and preprocess the image
    image = cv2.imread(image_path)
    original_size = image.shape[:2]  # Store original size
    
    # Use the size from your config
    IMAGE_SIZE = (384, 512)  # (Height, Width)
    resized = cv2.resize(image, (IMAGE_SIZE[1], IMAGE_SIZE[0])) / 255.0
    input_tensor = np.expand_dims(resized, axis=0)
    
    # Predict the mask
    pred_mask = model.predict(input_tensor)[0].squeeze()
    pred_mask = (pred_mask > 0.5).astype(np.uint8) * 255
    
    # Remove small noise
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(pred_mask, connectivity=8)
    sizes = stats[1:, -1]  # skip background
    min_size = 500  # tweak as needed
    new_mask = np.zeros_like(pred_mask)
    
    for i in range(1, num_labels):
        if sizes[i - 1] >= min_size:
            new_mask[labels == i] = 255
    
    # Optional: Smooth edges
    kernel = np.ones((3, 3), np.uint8)
    new_mask = cv2.morphologyEx(new_mask, cv2.MORPH_CLOSE, kernel)
    
    pred_mask = new_mask
    
    # Resize mask back to original size
    pred_mask = cv2.resize(pred_mask, (original_size[1], original_size[0]))
    
    # Create overlay
    overlay = overlay_mask_on_image(image_path, pred_mask)
    
    return overlay, pred_mask

def remove_shadows_web(image_path, mask):
    # Read the image
    image = cv2.imread(image_path)
    
    # Ensure mask is the right size and type
    if mask.shape[:2] != image.shape[:2]:
        mask = cv2.resize(mask, (image.shape[1], image.shape[0]))
    
    if len(mask.shape) == 2:
        mask = np.stack([mask, mask, mask], axis=-1)
    
    # Remove shadows
    result = remove_shadow(image_path, mask)
    
    return result

# ================== INITIALIZATION ==================

def init_db():
    with app.app_context():
        db.create_all()
        # Pre-load the model when the app starts
        load_shadow_model()

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
