from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import current_user, login_required
from functools import wraps
from datetime import datetime, timedelta
from models import User, ProcessedImage

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_required
def admin_dashboard():
    from app import db  
    users = User.query.all()
    users_data = []
    for user in users:
        processed_count = ProcessedImage.query.filter_by(user_id=user.id).count()
        last_activity = ProcessedImage.query.filter_by(user_id=user.id).order_by(ProcessedImage.created_at.desc()).first()
        users_data.append({
            'user': user,
            'processed_count': processed_count,
            'last_activity': last_activity
        })
    
    # Get recent activity (last 10)
    recent_activity = ProcessedImage.query.order_by(ProcessedImage.created_at.desc()).limit(10).all()
    
    # Get statistics
    total_users = User.query.count()
    total_processed = ProcessedImage.query.count()
    
    # Today's processed images
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_processed = ProcessedImage.query.filter(ProcessedImage.created_at >= today_start).count()
    
    # Weekly statistics
    week_start = today_start - timedelta(days=today_start.weekday())
    weekly_processed = ProcessedImage.query.filter(ProcessedImage.created_at >= week_start).count()
    
    # Process type statistics
    detection_count = ProcessedImage.query.filter_by(process_type='detection').count()
    removal_count = ProcessedImage.query.filter_by(process_type='removal').count()
    
    return render_template('admin/admin_dashboard.html', 
                         users_data=users_data,
                         recent_activity=recent_activity,
                         total_users=total_users,
                         total_processed=total_processed,
                         today_processed=today_processed,
                         weekly_processed=weekly_processed,
                         detection_count=detection_count,
                         removal_count=removal_count)

@admin_required
def admin_users():
    # Get search parameters
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    if search_query:
        users = User.query.filter(
            (User.username.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%')) |
            (User.first_name.ilike(f'%{search_query}%')) |
            (User.last_name.ilike(f'%{search_query}%'))
        ).order_by(User.created_at.desc())
    else:
        users = User.query.order_by(User.created_at.desc())
    
    # Paginate results
    users = users.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', users=users, search_query=search_query)

@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get processing statistics for this user
    processed_images = ProcessedImage.query.filter_by(user_id=user_id).order_by(ProcessedImage.created_at.desc()).all()
    detection_count = ProcessedImage.query.filter_by(user_id=user_id, process_type='detection').count()
    removal_count = ProcessedImage.query.filter_by(user_id=user_id, process_type='removal').count()
    
    # Get recent activity
    recent_activity = ProcessedImage.query.filter_by(user_id=user_id).order_by(ProcessedImage.created_at.desc()).limit(5).all()
    
    # Calculate user activity metrics
    if processed_images:
        first_activity = processed_images[-1].created_at
        days_active = (datetime.utcnow() - first_activity).days or 1
        avg_per_day = len(processed_images) / days_active
    else:
        first_activity = None
        days_active = 0
        avg_per_day = 0
    
    return render_template('admin/user_detail.html', 
                         user=user, 
                         processed_images=processed_images,
                         detection_count=detection_count,
                         removal_count=removal_count,
                         recent_activity=recent_activity,
                         first_activity=first_activity,
                         days_active=days_active,
                         avg_per_day=avg_per_day)

@admin_required
def admin_activity():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    user_id = request.args.get('user_id', type=int)
    process_type = request.args.get('process_type')
    date_filter = request.args.get('date_filter')
    
    # Build query
    query = ProcessedImage.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if process_type and process_type != 'all':
        query = query.filter_by(process_type=process_type)
    if date_filter:
        if date_filter == 'today':
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(ProcessedImage.created_at >= today_start)
        elif date_filter == 'week':
            week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
            query = query.filter(ProcessedImage.created_at >= week_start)
        elif date_filter == 'month':
            month_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
            query = query.filter(ProcessedImage.created_at >= month_start)
    
    processed_images = query.order_by(ProcessedImage.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    users = User.query.all()
    return render_template('admin/activity.html', 
                         processed_images=processed_images,
                         users=users,
                         user_id=user_id,
                         process_type=process_type,
                         date_filter=date_filter)

@admin_required
def admin_delete_image(image_id):
    from app import db  
    processed_image = ProcessedImage.query.get_or_404(image_id)
    user_id = processed_image.user_id
    
    try:
        # Delete the files from filesystem
        from app import app  # Import app instance
        processed_image.delete_files(app)
        
        # Delete from database
        db.session.delete(processed_image)
        db.session.commit()
        flash('Image deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting image: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin_activity'))

@admin_required
def admin_delete_user(user_id):
    from app import db  
    if current_user.id == user_id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        # First delete all user's processed images and their files
        from app import app  # Import app instance
        user_images = ProcessedImage.query.filter_by(user_id=user_id).all()
        for image in user_images:
            try:
                image.delete_files(app)
            except:
                pass  # Continue even if file deletion fails
            db.session.delete(image)
        
        # Then delete the user
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@admin_required
def admin_toggle_user_status(user_id):
    from app import db  
    if current_user.id == user_id:
        flash('You cannot modify your own account status', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        # Toggle user status (active/inactive)
        user.is_active = not user.is_active
        db.session.commit()
        
        status = "activated" if user.is_active else "deactivated"
        flash(f'User {user.username} has been {status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user status: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@admin_required
def admin_make_admin(user_id):
    from app import db  
    if current_user.id == user_id:
        flash('You cannot modify your own admin status', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        user.is_admin = True
        db.session.commit()
        flash(f'User {user.username} is now an administrator', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user admin status: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@admin_required
def admin_remove_admin(user_id):
    from app import db  
    if current_user.id == user_id:
        flash('You cannot remove your own admin privileges', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        user.is_admin = False
        db.session.commit()
        flash(f'Admin privileges removed from {user.username}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user admin status: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@admin_required
def admin_system_stats():
    from app import db  
    # User growth statistics
    user_growth_data = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).date()
        count = User.query.filter(db.func.date(User.created_at) <= date).count()
        user_growth_data.append({'date': date.strftime('%Y-%m-%d'), 'count': count})
    
    # Activity statistics
    activity_data = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).date()
        count = ProcessedImage.query.filter(db.func.date(ProcessedImage.created_at) == date).count()
        activity_data.append({'date': date.strftime('%Y-%m-%d'), 'count': count})
    
    # Process type distribution
    process_types = db.session.query(
        ProcessedImage.process_type, 
        db.func.count(ProcessedImage.id)
    ).group_by(ProcessedImage.process_type).all()
    
    # Top users by activity
    top_users = db.session.query(
        User.username,
        db.func.count(ProcessedImage.id).label('activity_count')
    ).join(ProcessedImage).group_by(User.id).order_by(db.desc('activity_count')).limit(10).all()
    
    return render_template('admin/system_stats.html',
                         user_growth_data=user_growth_data,
                         activity_data=activity_data,
                         process_types=process_types,
                         top_users=top_users)