class VideoAttendance {
    constructor(eventId) {
        this.eventId = eventId;
        this.video = document.getElementById('video');
        this.startBtn = document.getElementById('startCamera');
        this.captureBtn = document.getElementById('capture');
        this.stopBtn = document.getElementById('stopCamera');
        this.resultsDiv = document.getElementById('results');
        this.logEntries = document.getElementById('logEntries');
        this.totalRecognized = document.getElementById('totalRecognized');
        this.sessionCount = document.getElementById('sessionCount');
        
        this.stream = null;
        this.recognitionCount = 0;
        this.sessionRecognitionCount = 0;
        
        this.bindEvents();
    }
    
    bindEvents() {
        this.startBtn.addEventListener('click', () => this.startCamera());
        this.captureBtn.addEventListener('click', () => this.captureAndRecognize());
        this.stopBtn.addEventListener('click', () => this.stopCamera());
    }
    
    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 640, height: 480 } 
            });
            
            this.video.srcObject = this.stream;
            this.startBtn.disabled = true;
            this.captureBtn.disabled = false;
            this.stopBtn.disabled = false;
            
            this.showMessage('Camera started successfully!', 'success');
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showMessage('Error accessing camera. Please check permissions.', 'error');
        }
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.video.srcObject = null;
            this.startBtn.disabled = false;
            this.captureBtn.disabled = true;
            this.stopBtn.disabled = true;
            
            this.showMessage('Camera stopped.', 'info');
        }
    }
    
    captureAndRecognize() {
        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;
        const context = canvas.getContext('2d');
        
        context.drawImage(this.video, 0, 0, canvas.width, canvas.height);
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        
        this.processAttendance(imageData);
    }
    
    async processAttendance(imageData) {
        this.showMessage('Processing face recognition...', 'info');
        this.captureBtn.disabled = true;
        
        try {
            const response = await fetch('/api/process_attendance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    event_id: this.eventId,
                    image: imageData
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.recognitionCount += data.count;
                this.sessionRecognitionCount += data.count;
                this.totalRecognized.textContent = this.recognitionCount;
                this.sessionCount.textContent = this.sessionRecognitionCount;
                
                this.showMessage(data.message, 'success');
                
                if (data.recognized_members && data.recognized_members.length > 0) {
                    data.recognized_members.forEach(member => {
                        this.addLogEntry(member);
                    });
                }
            } else {
                this.showMessage(data.message, 'warning');
            }
        } catch (error) {
            console.error('Error processing attendance:', error);
            this.showMessage('Error processing recognition', 'error');
        } finally {
            this.captureBtn.disabled = false;
        }
    }
    
    showMessage(message, type) {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        this.resultsDiv.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show">
                <i class="fas fa-${this.getMessageIcon(type)}"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }
    
    getMessageIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    addLogEntry(memberData) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = 'border-bottom py-1';
        logEntry.innerHTML = `
            <small>
                <i class="fas fa-user-check text-success"></i>
                <strong>${memberData.name}</strong>
                <span class="text-muted">(${memberData.confidence}%)</span>
                <span class="text-muted float-end">${timestamp}</span>
            </small>
        `;
        
        this.logEntries.prepend(logEntry);
        
        if (this.logEntries.children.length > 10) {
            this.logEntries.removeChild(this.logEntries.lastChild);
        }
    }
}

function initVideoAttendance(eventId) {
    return new VideoAttendance(eventId);
}