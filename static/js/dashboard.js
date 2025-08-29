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
    
    // Variables
    let uploadedFile = null;
    let currentMode = null;
    
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
            // Show preview
            previewImage.src = e.target.result;
            
            // Update UI
            uploadPlaceholder.classList.add('d-none');
            imagePreviewSection.classList.remove('d-none');
            
            // Display image info
            displayImageInfo(file);
            
            // Clear previous results
            clearResults();
            
            // Enable detection button
            detectBtn.disabled = false;
            processingInfo.classList.remove('d-none');
            
            showNotification('Image uploaded successfully', 'success');
        };
        reader.readAsDataURL(file);
    }
    
    function displayImageInfo(file) {
        const img = new Image();
        img.src = URL.createObjectURL(file);
        img.onload = function() {
            const fileSize = formatFileSize(file.size);
            const dimensions = `${img.width} × ${img.height} pixels`;
            const format = file.type.split('/')[1].toUpperCase();
            
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
                    <span>${dimensions}</span>
                </div>
                <div class="d-flex justify-content-between">
                    <span>Format:</span>
                    <span>${format}</span>
                </div>
            `;
            
            URL.revokeObjectURL(img.src);
        };
    }
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' bytes';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }
    
    function clearImage() {
        fileInput.value = '';
        uploadedFile = null;
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