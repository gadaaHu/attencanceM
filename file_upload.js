// File upload utilities
class FileUpload {
    static validateFile(file, allowedTypes, maxSize) {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            return { valid: false, message: `File type not allowed. Allowed types: ${allowedTypes.join(', ')}` };
        }
        
        if (file.size > maxSize) {
            return { valid: false, message: `File too large. Maximum size: ${maxSize / 1024 / 1024}MB` };
        }
        
        return { valid: true };
    }
    
    static previewImage(file, previewElementId) {
        const reader = new FileReader();
        const preview = document.getElementById(previewElementId);
        
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
        
        reader.readAsDataURL(file);
    }
    
    static showUploadProgress(progressElementId, percentage) {
        const progress = document.getElementById(progressElementId);
        if (progress) {
            progress.style.width = percentage + '%';
            progress.textContent = percentage + '%';
        }
    }
}