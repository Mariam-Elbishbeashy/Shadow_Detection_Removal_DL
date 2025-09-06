// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const fileInput = document.getElementById('fileInput');
    const selectImageBtn = document.getElementById('selectImageBtn');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    const imagePreviewSection = document.getElementById('imagePreviewSection');
    const previewImage = document.getElementById('previewImage');
    const changeImageBtn = document.getElementById('changeImageBtn');
    const imageInfoContent = document.getElementById('imageInfoContent');
    const processedImagePlaceholder = document.getElementById('processedImagePlaceholder');
    const detectBtn = document.getElementById('detectBtn');
    const removeBtn = document.getElementById('removeBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const processingInfo = document.getElementById('processingInfo');
    
    // Size constraints
    const MAX_WIDTH = 640;
    const MAX_HEIGHT = 480;
    const MIN_WIDTH = 100;
    const MIN_HEIGHT = 100;
    
    // Variables
    let uploadedFile = null;
    let currentMode = null;
    let imageWidth = 0;
    let imageHeight = 0;
    
    // Event Listeners
    selectImageBtn.addEventListener('click', () => fileInput.click());
    changeImageBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    detectBtn.addEventListener('click', detectShadows);
    removeBtn.addEventListener('click', removeShadows);
    downloadBtn.addEventListener('click', downloadResult);
    
    // Functions
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file || !file.type.match('image.*')) {
            showNotification('Please select a valid image file (JPEG, PNG, etc.)', 'error');
            return;
        }
        
        // Check file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            showNotification('File size must be less than 10MB', 'error');
            return;
        }
        
        uploadedFile = file;
        const reader = new FileReader();
        reader.onload = function(e) {
            // Create image to get dimensions
            const img = new Image();
            img.onload = function() {
                imageWidth = img.width;
                imageHeight = img.height;
                
                // Validate image dimensions
                const validationResult = validateImageDimensions(imageWidth, imageHeight);
                if (!validationResult.isValid) {
                    showNotification(validationResult.message, 'warning');
                    // Still show preview but disable processing
                    showImagePreview(e.target.result, file, false);
                    return;
                }
                
                // Show preview and enable processing
                showImagePreview(e.target.result, file, true);
                
                if (validationResult.warning) {
                    showNotification(validationResult.warning, 'info');
                }
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    function validateImageDimensions(width, height) {
        if (width > MAX_WIDTH || height > MAX_HEIGHT) {
            return {
                isValid: false,
                message: `Image is too large (${width}×${height}). Maximum allowed: ${MAX_WIDTH}×${MAX_HEIGHT}px.`
            };
        }
        
        if (width < MIN_WIDTH || height < MIN_HEIGHT) {
            return {
                isValid: false,
                message: `Image is too small (${width}×${height}). Minimum required: ${MIN_WIDTH}×${MIN_HEIGHT}px.`
            };
        }
        
        // Check if image is relatively small and might have quality issues
        if (width < 300 || height < 300) {
            return {
                isValid: true,
                warning: `Note: Image is relatively small (${width}×${height}px). Results may have lower quality.`
            };
        }
        
        return { isValid: true };
    }
    
    function showImagePreview(imageSrc, file, enableProcessing) {
        // Show preview
        previewImage.src = imageSrc;
        
        // Update UI
        uploadPlaceholder.classList.add('d-none');
        imagePreviewSection.classList.remove('d-none');
        
        // Display image info
        displayImageInfo(file);
        
        // Clear previous results
        clearResults();
        
        // Enable/disable detection button based on validation
        detectBtn.disabled = !enableProcessing;
        processingInfo.classList.remove('d-none');
        
        if (enableProcessing) {
            showNotification('Image uploaded successfully', 'success');
        }
    }
    
    function displayImageInfo(file) {
        const fileSize = formatFileSize(file.size);
        const dimensions = `${imageWidth} × ${imageHeight} pixels`;
        const format = file.type.split('/')[1].toUpperCase();
        
        // Add dimension validation status
        let dimensionStatus = '';
        if (imageWidth > MAX_WIDTH || imageHeight > MAX_HEIGHT) {
            dimensionStatus = '<span class="text-danger">❌ Too large</span>';
        } else if (imageWidth < MIN_WIDTH || imageHeight < MIN_HEIGHT) {
            dimensionStatus = '<span class="text-danger">❌ Too small</span>';
        } else if (imageWidth < 300 || imageHeight < 300) {
            dimensionStatus = '<span class="text-warning">⚠️ Low resolution</span>';
        } else {
            dimensionStatus = '<span class="text-success">✅ Good</span>';
        }
        
        imageInfoContent.innerHTML = `
            <div class="d-flex justify-content-between mb-1">
                <span>Name:</span>
                <span>${file.name}</span>
            </div>
            <div class="d-flex justify-content-between mb-1">
                <span>Size:</span>
                <span>${fileSize}</span>
            </div>
            <div class="d-flex justify-content-between mb-1">
                <span>Dimensions:</span>
                <span>${dimensions} ${dimensionStatus}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>Format:</span>
                <span>${format}</span>
            </div>
        `;
    }
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' bytes';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }
    
    function clearImage() {
        fileInput.value = '';
        uploadedFile = null;
        imageWidth = 0;
        imageHeight = 0;
        uploadPlaceholder.classList.remove('d-none');
        imagePreviewSection.classList.add('d-none');
        clearResults();
        showNotification('Image cleared', 'info');
    }
    
    function clearResults() {
        processedImagePlaceholder.innerHTML = `
            <div>
                <i class="fas fa-image display-4 text-muted mb-3"></i>
                <p class="text-muted">Processed image will appear here</p>
            </div>
        `;
        disableProcessingButtons();
        processingInfo.classList.add('d-none');
    }
    
    function detectShadows() {
        if (!uploadedFile) return;
        
        // Double-check dimensions before processing
        const validationResult = validateImageDimensions(imageWidth, imageHeight);
        if (!validationResult.isValid) {
            showNotification(validationResult.message, 'error');
            return;
        }
        
        currentMode = 'detection';
        
        // Show loading state
        setButtonLoading(detectBtn, 'Detecting...');
        disableProcessingButtons();
        showProcessingState('Detecting shadows...', 'primary');
        
        // Create FormData with the image
        const formData = new FormData();
        formData.append('image', uploadedFile);
        
        // Call detection endpoint
        fetch('/detect', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Detection failed');
            }
            return response.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            
            processedImagePlaceholder.innerHTML = `
                <div class="position-relative">
                    <img src="${url}" class="img-fluid rounded shadow-sm" style="max-height: 300px;">
                    <span class="badge bg-primary position-absolute top-0 start-0 m-2">Shadow Detection</span>
                </div>
            `;
            
            // Enable download and remove buttons
            downloadBtn.disabled = false;
            removeBtn.disabled = false;
            
            // Reset button state
            setButtonReady(detectBtn, 'Detect Shadows');
            
            showNotification('Shadow detection completed successfully', 'success');
        })
        .catch(error => {
            showProcessingState('Error processing image', 'danger');
            setButtonReady(detectBtn, 'Detect Shadows');
            removeBtn.disabled = false;
            showNotification('Error detecting shadows: ' + error.message, 'error');
            console.error('Detection error:', error);
        });
    }
    
    function removeShadows() {
        if (!uploadedFile) return;
        
        // Double-check dimensions before processing
        const validationResult = validateImageDimensions(imageWidth, imageHeight);
        if (!validationResult.isValid) {
            showNotification(validationResult.message, 'error');
            return;
        }
        
        currentMode = 'removal';
        
        // Show loading state
        setButtonLoading(removeBtn, 'Removing...');
        disableProcessingButtons();
        showProcessingState('Removing shadows...', 'success');
        
        // Create FormData with the image
        const formData = new FormData();
        formData.append('image', uploadedFile);
        
        // Call removal endpoint
        fetch('/remove', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Removal failed');
            }
            return response.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            
            processedImagePlaceholder.innerHTML = `
                <div class="position-relative">
                    <img src="${url}" class="img-fluid rounded shadow-sm" style="max-height: 300px;">
                    <span class="badge bg-success position-absolute top-0 start-0 m-2">Shadow Removal</span>
                </div>
            `;
            
            // Enable download button
            downloadBtn.disabled = false;
            
            // Reset button state
            setButtonReady(removeBtn, 'Remove Shadows');
            
            showNotification('Shadows removed successfully', 'success');
        })
        .catch(error => {
            showProcessingState('Error removing shadows', 'danger');
            setButtonReady(removeBtn, 'Remove Shadows');
            showNotification('Error removing shadows: ' + error.message, 'error');
            console.error('Removal error:', error);
        });
    }
    
    function downloadResult() {
        const imageElement = processedImagePlaceholder.querySelector('img');
        if (!imageElement) return;
        
        const imageSrc = imageElement.src;
        const link = document.createElement('a');
        link.href = imageSrc;
        
        // Create a proper filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const originalName = uploadedFile?.name?.split('.')[0] || 'image';
        const extension = 'jpg';
        link.download = `${originalName}_${currentMode}_${timestamp}.${extension}`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification('Download started', 'success');
    }
    
    function disableProcessingButtons() {
        detectBtn.disabled = true;
        removeBtn.disabled = true;
        downloadBtn.disabled = true;
    }
    
    function setButtonLoading(button, text) {
        button.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${text}`;
        button.disabled = true;
    }
    
    function setButtonReady(button, text) {
        button.innerHTML = text;
        button.disabled = false;
    }
    
    function showProcessingState(message, type) {
        processedImagePlaceholder.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-${type}" role="status"></div>
                <p class="mt-2 text-${type}">${message}</p>
            </div>
        `;
    }
    
    function showNotification(message, type) {
        // Remove any existing notifications first
        document.querySelectorAll('.alert.position-fixed').forEach(alert => {
            alert.remove();
        });
        
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
});