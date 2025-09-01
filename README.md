# Shadow Detection and Removal Application

![Python](https://img.shields.io/badge/Python-3.8%252B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0%252B-orange)
![OpenCV](https://img.shields.io/badge/OpenCV-4.0%252B-red)

A comprehensive web application for detecting and removing shadows from images using deep learning models. This Flask-based application provides both a user-friendly web interface and RESTful API endpoints for image processing operations.

---

## ✨ Features

* 🔐 **User Authentication:** Secure login/signup system with user profiles
* 🕵️ **Shadow Detection:** AI-powered shadow detection in uploaded images
* ✨ **Shadow Removal:** Advanced shadow removal functionality
* 📊 **Processing History:** Track all processed images with timestamps
* 👨‍💼 **Admin Dashboard:** Comprehensive admin interface for user management
* 🔌 **RESTful API:** JSON API for integration with other applications
* 📱 **Responsive Design:** Bootstrap-based UI that works on all devices
* 📈 **Activity Monitoring:** Track user activity and system statistics
* 🎯 **Role-Based Access:** Admin and user roles with appropriate permissions

---

## 🛠️ Technology Stack

* **Backend:** Flask (Python web framework)
* **Database:** SQLite with SQLAlchemy ORM
* **Authentication:** Flask-Login for session management
* **Image Processing:** OpenCV, TensorFlow/Keras
* **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
* **File Handling:** Werkzeug for secure file uploads

---

## 📦 Installation

### Prerequisites

* Python 3.8 or higher
* `pip` (Python package manager)

### Step-by-Step Setup

**1) Clone the repository**

```bash
git clone <your-repository-url>
cd shadow-removal-app
```

**2) Create and activate a virtual environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**3) Install dependencies**

```bash
pip install -r requirements.txt
```

**4) Initialize the database**

```bash
python init_db.py
```

**5) Run the application**

```bash
python app.py
```

**6) Access the application**

Open your browser and navigate to: `http://localhost:5000`

---

## 🔧 Configuration

The application uses the following configuration settings (in `app.py`):

```python
app.config['SECRET_KEY'] = 'your-secret-key-here'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shadow_app.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'static/results'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB file limit
```

---

## 📁 Project Structure

```text
shadow-removal-app/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── models.py             # Database models (User, ProcessedImage)
├── admin_route.py        # Admin functionality routes
├── shadow_detection.py   # Shadow detection model and functions
├── shadow_removal.py     # Shadow removal algorithms
├── init_db.py           # Database initialization script
├── static/
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   ├── images/          # Static images
│   ├── uploads/         # User uploaded files
│   └── results/         # Processed images storage
├── templates/
│   ├── base.html        # Base template
│   ├── index.html       # Home page
│   ├── login.html       # Login page
│   ├── signup.html      # Registration page
│   ├── dashboard.html   # User dashboard
│   ├── history.html     # Processing history
│   ├── profile.html     # User profile
│   ├── documentation.html # API documentation
│   ├── help.html        # Help page
│   ├── access_denied.html 
│   └── admin/           # Admin templates
│       ├── dashboard.html
│       ├── users.html
│       ├── user_detail.html
│       ├── activity.html
│       └── system_stats.html
└── README.md            # This file
```

---

## 🚀 Usage

### For End Users

1. **Register/Login:** Create an account or login to existing account
2. **Upload Image:** Use the dashboard to upload an image for processing
3. **Process Image:** Choose between shadow detection or removal
4. **View Results:** See processed images and download results
5. **Manage History:** View and delete previous processing jobs

### For Administrators

* **Access Admin Dashboard:** Navigate to `/admin` after logging in as admin
* **User Management:** View, promote, demote, or delete users
* **Activity Monitoring:** Track all processing activity across the system
* **System Statistics:** View usage metrics and system performance

---

## 🔌 API Usage

The application provides RESTful API endpoints:

```bash
# Authentication
POST /login - User login
POST /signup - User registration

# Image Processing
POST /detect - Detect shadows in image
POST /remove - Remove shadows from image

# Image Management
GET /history - Get processing history
GET /view_image/<id> - View processed image
GET /download_image/<id> - Download processed image
POST /delete_image/<id> - Delete processed image

# API Documentation
GET /api/docs - Complete API documentation
```

**Example API request for shadow detection:**

```bash
curl -X POST -F "image=@path/to/your/image.jpg" http://localhost:5000/detect
```

---

## 🧠 Machine Learning Models

The application uses a pre-trained deep learning model for shadow detection:

* **Model Architecture:** Custom CNN based on U-Net architecture
* **Training:** Model trained on augmented shadow detection dataset
* **Performance:** Achieves high Dice coefficient and IoU scores
* **File:** `shadow_model2_0850_K2S2E5_aug.h5`

The shadow removal process combines traditional computer vision techniques with the detection model's output to effectively remove shadows while preserving image quality.

---

## 🔒 Security Features

* Password hashing with Werkzeug security utilities
* SQL injection prevention through SQLAlchemy ORM
* File upload validation and sanitization
* Authentication required for protected routes
* Admin role-based access control
* CSRF protection for forms
* Secure session management

---

## 📊 Database Schema

### Users Table

* `id` (Integer, Primary Key)
* `username` (String, Unique)
* `email` (String, Unique)
* `password_hash` (String)
* `first_name` (String)
* `last_name` (String)
* `avatar` (String)
* `bio` (Text)
* `created_at` (DateTime)
* `updated_at` (DateTime)
* `is_admin` (Boolean)
* `is_active` (Boolean)

### ProcessedImages Table

* `id` (Integer, Primary Key)
* `user_id` (Integer, Foreign Key)
* `original_filename` (String)
* `processed_filename` (String)
* `process_type` (String) - 'detection' or 'removal'
* `created_at` (DateTime)

---

## 📈 Performance Notes

* The shadow detection model requires significant memory
* Large images may take several seconds to process
* Consider implementing background task processing for production
* Enable gzip compression for static assets
* Implement caching for frequently accessed resources

---

## 🔮 Future Enhancements

* Batch processing of multiple images
* Additional image enhancement features
* Mobile application interface
* Cloud storage integration
* Advanced user analytics
* Plugin system for custom processing algorithms

