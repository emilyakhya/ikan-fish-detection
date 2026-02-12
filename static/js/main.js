// IKAN Fish Detection - Frontend JavaScript

// Global state
let currentFile = null;
let currentFileName = null;
let currentFileType = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const filePreview = document.getElementById('filePreview');
const previewImage = document.getElementById('previewImage');
const previewVideo = document.getElementById('previewVideo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const fileType = document.getElementById('fileType');
const clearPreviewBtn = document.getElementById('clearPreviewBtn');
const confSlider = document.getElementById('confSlider');
const confValue = document.getElementById('confValue');
const weightsSelect = document.getElementById('weightsSelect');
const imgszSelect = document.getElementById('imgszSelect');
const detectBtn = document.getElementById('detectBtn');
const resultsSection = document.getElementById('resultsSection');
const resultImage = document.getElementById('resultImage');
const resultVideo = document.getElementById('resultVideo');
const statsGrid = document.getElementById('statsGrid');
const downloadBtn = document.getElementById('downloadBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const progressFill = document.getElementById('progressFill');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadAvailableWeights();
    setupEventListeners();
});

// Load available model weights
async function loadAvailableWeights() {
    try {
        const response = await fetch('/api/weights');
        const data = await response.json();
        
        weightsSelect.innerHTML = '';
        data.weights.forEach(weight => {
            const option = document.createElement('option');
            option.value = weight.path;
            option.textContent = weight.name;
            weightsSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading weights:', error);
        showNotification('Error loading model weights', 'error');
    }
}

// Setup event listeners
function setupEventListeners() {
    // File input
    selectFileBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // Clear preview
    clearPreviewBtn.addEventListener('click', clearPreview);
    
    // Confidence slider
    confSlider.addEventListener('input', (e) => {
        confValue.textContent = parseFloat(e.target.value).toFixed(2);
    });
    
    // Detect button
    detectBtn.addEventListener('click', runDetection);
    
    // Download button
    downloadBtn.addEventListener('click', downloadResult);
}

// Handle file selection
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        processFile(file);
    }
}

// Handle drag over
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('dragover');
}

// Handle drag leave
function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
}

// Handle drop
function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

// Process uploaded file
async function processFile(file) {
    // Validate file
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
        showNotification('File terlalu besar! Maksimal 100MB', 'error');
        return;
    }
    
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
                          'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Format file tidak didukung!', 'error');
        return;
    }
    
    currentFile = file;
    currentFileName = file.name;
    currentFileType = file.type.startsWith('image/') ? 'image' : 'video';
    
    // Display preview
    displayPreview(file);
    
    // Upload file to server
    await uploadFile(file);
}

// Display file preview
function displayPreview(file) {
    filePreview.style.display = 'block';
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileType.textContent = currentFileType === 'image' ? 'Gambar' : 'Video';
    
    const reader = new FileReader();
    
    if (currentFileType === 'image') {
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewImage.style.display = 'block';
            previewVideo.style.display = 'none';
        };
        reader.readAsDataURL(file);
    } else {
        previewVideo.src = URL.createObjectURL(file);
        previewVideo.style.display = 'block';
        previewImage.style.display = 'none';
    }
    
    detectBtn.disabled = false;
}

// Upload file to server
async function uploadFile(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentFileName = data.filename;
            showNotification('File berhasil diupload!', 'success');
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Error uploading file: ' + error.message, 'error');
        clearPreview();
    }
}

// Run detection
async function runDetection() {
    if (!currentFileName) {
        showNotification('Silakan upload file terlebih dahulu!', 'error');
        return;
    }
    
    // Show loading
    showLoading('Memproses deteksi...');
    
    try {
        const confThres = parseFloat(confSlider.value);
        const weights = weightsSelect.value;
        const imgsz = parseInt(imgszSelect.value);
        
        const response = await fetch('/api/detect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentFileName,
                conf_thres: confThres,
                weights: weights,
                imgsz: imgsz
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update progress
            updateProgress(100);
            
            // Display results
            await displayResults(data);
            
            showNotification('Deteksi berhasil!', 'success');
        } else {
            throw new Error(data.error || 'Detection failed');
        }
    } catch (error) {
        console.error('Detection error:', error);
        showNotification('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Display detection results
async function displayResults(data) {
    resultsSection.style.display = 'block';
    
    // Info message is always shown (no conditional display)
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Display statistics
    displayStats(data);
    
    // Display result image/video
    const resultUrl = `/api/results/${data.result_path}`;
    
    if (data.type === 'image') {
        resultImage.src = resultUrl;
        resultImage.style.display = 'block';
        resultVideo.style.display = 'none';
    } else {
        resultVideo.src = resultUrl;
        resultVideo.style.display = 'block';
        resultImage.style.display = 'none';
    }
    
    // Setup download button
    downloadBtn.style.display = 'inline-block';
    downloadBtn.onclick = () => {
        const link = document.createElement('a');
        link.href = resultUrl;
        link.download = data.result_file;
        link.click();
    };
}

// Display statistics
function displayStats(data) {
    statsGrid.innerHTML = '';
    
    // Total detections
    const totalCard = createStatCard('Total Deteksi', data.detection_count || 0);
    statsGrid.appendChild(totalCard);
    
    // Detection count by class
    if (data.detections && data.detections.length > 0) {
        const classCounts = {};
        const classConfidences = {};
        
        data.detections.forEach(det => {
            const className = det.class_name || `Class_${det.class}` || 'Unknown';
            classCounts[className] = (classCounts[className] || 0) + 1;
            if (!classConfidences[className]) {
                classConfidences[className] = [];
            }
            classConfidences[className].push(det.confidence || 0);
        });
        
        // Display counts and average confidence per class
        Object.entries(classCounts).forEach(([className, count]) => {
            const avgConf = classConfidences[className].reduce((sum, c) => sum + c, 0) / classConfidences[className].length;
            
            // Display class name only (no original detection info)
            const card = createStatCard(className, `${count} (${(avgConf * 100).toFixed(1)}%)`);
            statsGrid.appendChild(card);
        });
        
        // Overall average confidence
        const avgConf = data.detections.reduce((sum, d) => sum + (d.confidence || 0), 0) / data.detections.length;
        const confCard = createStatCard('Confidence Rata-rata', (avgConf * 100).toFixed(1) + '%');
        statsGrid.appendChild(confCard);
    }
}

// Create stat card element
function createStatCard(label, value) {
    const card = document.createElement('div');
    card.className = 'stat-card';
    card.innerHTML = `
        <h4>${label}</h4>
        <div class="stat-value">${value}</div>
    `;
    return card;
}

// Download result
function downloadResult() {
    const resultUrl = resultImage.style.display !== 'none' 
        ? resultImage.src 
        : resultVideo.src;
    
    const link = document.createElement('a');
    link.href = resultUrl;
    link.download = 'detection_result';
    link.click();
}

// Clear preview
function clearPreview() {
    currentFile = null;
    currentFileName = null;
    currentFileType = null;
    filePreview.style.display = 'none';
    previewImage.src = '';
    previewVideo.src = '';
    fileInput.value = '';
    detectBtn.disabled = true;
    resultsSection.style.display = 'none';
}

// Show loading overlay
function showLoading(text = 'Memproses...') {
    loadingText.textContent = text;
    loadingOverlay.style.display = 'flex';
    updateProgress(0);
    
    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        updateProgress(progress);
    }, 500);
    
    // Store interval to clear later
    window.loadingInterval = interval;
}

// Hide loading overlay
function hideLoading() {
    loadingOverlay.style.display = 'none';
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
        window.loadingInterval = null;
    }
    updateProgress(0);
}

// Update progress bar
function updateProgress(percent) {
    progressFill.style.width = percent + '%';
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#0066cc'};
        color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
