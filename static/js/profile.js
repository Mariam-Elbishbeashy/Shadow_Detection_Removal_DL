// profile.js - User Profile JavaScript with Database Integration

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form validation and interactions
    initProfileForms();
    initPasswordStrength();
    initNavigation();
    initAvatarUpload();
    loadProfileData();
});

function initProfileForms() {
    // Profile form submission
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveProfileChanges();
        });
    }

    // Security form submission
    const securityForm = document.getElementById('securityForm');
    if (securityForm) {
        securityForm.addEventListener('submit', function(e) {
            e.preventDefault();
            updatePassword();
        });
    }
}

function loadProfileData() {
    // Populate form fields with current user data
    document.getElementById('firstName').value = document.getElementById('firstName').dataset.value || '';
    document.getElementById('lastName').value = document.getElementById('lastName').dataset.value || '';
    document.getElementById('bio').value = document.getElementById('bio').dataset.value || '';
}

function initPasswordStrength() {
    const passwordInput = document.getElementById('newPassword');
    const strengthBar = document.querySelector('.password-strength .progress-bar');
    const strengthText = document.querySelector('.password-strength-text');

    if (passwordInput && strengthBar && strengthText) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = calculatePasswordStrength(password);
            
            updateStrengthDisplay(strength, strengthBar, strengthText);
        });
    }
}

function calculatePasswordStrength(password) {
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength += 20;
    if (password.length >= 12) strength += 20;
    
    // Character variety checks
    if (/[A-Z]/.test(password)) strength += 20;
    if (/[0-9]/.test(password)) strength += 20;
    if (/[^A-Za-z0-9]/.test(password)) strength += 20;
    
    return Math.min(strength, 100);
}

function updateStrengthDisplay(strength, bar, text) {
    bar.style.width = strength + '%';
    
    if (strength < 40) {
        bar.className = 'progress-bar bg-danger';
        text.textContent = 'Weak password';
    } else if (strength < 70) {
        bar.className = 'progress-bar bg-warning';
        text.textContent = 'Medium password';
    } else {
        bar.className = 'progress-bar bg-success';
        text.textContent = 'Strong password';
    }
}

function initNavigation() {
    // Smooth scrolling for navigation
    const navLinks = document.querySelectorAll('.profile-nav .nav-link');
    const sections = document.querySelectorAll('.profile-section');
    
    // Set active section on scroll
    window.addEventListener('scroll', function() {
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (window.scrollY >= (sectionTop - 100)) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').substring(1) === current) {
                link.classList.add('active');
            }
        });
    });
    
    // Smooth scroll on click
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function initAvatarUpload() {
    const avatarOverlay = document.querySelector('.avatar-overlay');
    const avatarInput = document.createElement('input');
    avatarInput.type = 'file';
    avatarInput.accept = 'image/*';
    avatarInput.name = 'avatar';
    avatarInput.style.display = 'none';
    
    if (avatarOverlay) {
        avatarOverlay.addEventListener('click', function() {
            avatarInput.click();
        });
        
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                uploadAvatar(file);
            }
        });
        
        document.body.appendChild(avatarInput);
    }
}

function initAvatarUpload() {
    const avatarOverlay = document.querySelector('.avatar-overlay');
    const avatarInput = document.createElement('input');
    avatarInput.type = 'file';
    avatarInput.name = 'avatar';
    avatarInput.accept = 'image/*';
    avatarInput.style.display = 'none';
    
    if (avatarOverlay) {
        avatarOverlay.addEventListener('click', function() {
            avatarInput.click();
        });
        
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Check file size
                if (file.size > 2 * 1024 * 1024) {
                    showNotification('File size must be less than 2MB', 'error');
                    return;
                }
                
                // Preview image
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('avatarPreview').src = e.target.result;
                };
                reader.readAsDataURL(file);
                
                // Upload to server
                uploadAvatar(file);
            }
        });
        
        document.body.appendChild(avatarInput);
    }
}

function uploadAvatar(file) {
    const formData = new FormData();
    formData.append('avatar', file);
    
    showLoading('Uploading avatar...');
    
    fetch('/api/profile/upload-avatar', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification('Avatar updated successfully!', 'success');
            // Update avatar preview with the new URL
            if (data.avatar_url) {
                document.getElementById('avatarPreview').src = data.avatar_url;
            }
        } else {
            showNotification(data.message || 'Error uploading avatar', 'error');
            // Revert to original avatar on error
            document.getElementById('avatarPreview').src = document.getElementById('avatarPreview').dataset.original;
        }
    })
    .catch(error => {
        console.error('Error uploading avatar:', error);
        hideLoading();
        showNotification('Error uploading avatar', 'error');
    });
}

function saveProfileChanges() {
    const email = document.getElementById('email').value;
    const firstName = document.getElementById('firstName').value;
    const lastName = document.getElementById('lastName').value;
    const bio = document.getElementById('bio').value;
    
    showLoading('Saving profile changes...');
    
    // Make API call to update profile
    fetch('/api/profile/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            first_name: firstName,
            last_name: lastName,
            bio: bio
        }),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification('Profile updated successfully!', 'success');
        } else {
            showNotification(data.message || 'Error updating profile', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating profile:', error);
        hideLoading();
        showNotification('Error updating profile', 'error');
    });
}

function updatePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (newPassword !== confirmPassword) {
        showNotification('Passwords do not match!', 'error');
        return;
    }
    
    showLoading('Updating password...');
    
    // Make API call to update password
    fetch('/api/profile/update-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
            confirm_password: confirmPassword
        }),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification('Password updated successfully!', 'success');
            
            // Clear form
            document.getElementById('securityForm').reset();
            document.querySelector('.password-strength .progress-bar').style.width = '0%';
            document.querySelector('.password-strength-text').textContent = 'Password strength';
        } else {
            showNotification(data.message || 'Error updating password', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating password:', error);
        hideLoading();
        showNotification('Error updating password', 'error');
    });
}

// Utility functions
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function showLoading(message) {
    // Create or show loading indicator
    let loading = document.getElementById('loadingIndicator');
    if (!loading) {
        loading = document.createElement('div');
        loading.id = 'loadingIndicator';
        loading.className = 'loading-indicator';
        loading.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span>${message}</span>
        `;
        document.body.appendChild(loading);
    }
    loading.style.display = 'flex';
}

function hideLoading() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) {
        loading.style.display = 'none';
    }
}