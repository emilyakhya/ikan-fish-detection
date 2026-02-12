#!/usr/bin/env python3
"""
Flask Web Application for IKAN Fish Detection
Provides web interface for YOLOv5 fish species detection
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import torch
from PIL import Image

# Add yolov5 to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / 'yolov5'))

app = Flask(__name__)
CORS(app)

# Class names for 2-class detection (Fish, notFish)
CLASS_NAMES = {
    0: 'Fish',
    1: 'notFish'
}

# COCO class names (for mapping COCO detections to Fish/notFish)
COCO_CLASS_NAMES = {
    0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus',
    6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant',
    11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat',
    16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear',
    22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag',
    27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard',
    32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove',
    36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle',
    40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon',
    45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 49: 'orange',
    50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut',
    55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed',
    60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse',
    65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave', 69: 'oven',
    70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock',
    75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'
}

def map_coco_to_fish_notfish(class_id, class_name=None):
    """
    Map COCO class detections to Fish/notFish
    Since COCO doesn't have fish, we'll classify:
    - Boat (8) in water context might be notFish
    - Everything else is notFish
    - If we detect something that could be fish-like, we'll need heuristics
    """
    # COCO class 8 is 'boat' - in underwater context, this is notFish
    # All other COCO classes are definitely notFish
    # Since COCO doesn't detect fish, we need to use heuristics
    
    # For now, map everything to notFish since COCO doesn't have fish class
    # In a real scenario, you'd need a trained fish detection model
    return 1  # notFish

def convert_coco_detections_to_fish_notfish(detections):
    """
    Convert COCO format detections to Fish/notFish format
    This is a temporary solution until a proper fish model is trained
    """
    converted = []
    for det in detections:
        coco_class_id = det.get('class', 0)
        coco_class_name = COCO_CLASS_NAMES.get(coco_class_id, f'class_{coco_class_id}')
        
        # Map to Fish/notFish
        fish_class_id = map_coco_to_fish_notfish(coco_class_id, coco_class_name)
        
        converted.append({
            'class': fish_class_id,
            'class_name': CLASS_NAMES[fish_class_id],
            'original_coco_class': coco_class_name,
            'original_coco_id': coco_class_id,
            'confidence': det.get('confidence', 0),
            'bbox': det.get('bbox', [])
        })
    
    return converted

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = BASE_DIR / 'uploads'
app.config['RESULTS_FOLDER'] = BASE_DIR / 'results'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'mkv'}

# Create necessary directories
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['RESULTS_FOLDER'].mkdir(exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_image_file(filename):
    """Check if file is an image"""
    return filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def is_video_file(filename):
    """Check if file is a video"""
    return filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov', 'mkv'}

def convert_heif_to_png(filepath):
    """Convert HEIF/HEIC files to PNG format"""
    try:
        # Check if file is actually HEIF/HEIC
        result = subprocess.run(
            ['file', str(filepath)],
            capture_output=True,
            text=True
        )
        
        if 'HEIF' in result.stdout or 'HEIC' in result.stdout:
            # Convert using sips (macOS) or pillow-heif
            output_path = filepath.with_suffix('.png')
            
            # Try sips first (macOS)
            result = subprocess.run(
                ['sips', '-s', 'format', 'png', str(filepath), '--out', str(output_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and output_path.exists():
                # Remove original and rename converted file
                filepath.unlink()
                return output_path
            
            # Try PIL with pillow-heif if available
            try:
                img = Image.open(filepath)
                output_path = filepath.with_suffix('.png')
                img.save(output_path, 'PNG')
                filepath.unlink()
                return output_path
            except Exception:
                pass
        
        return filepath
    except Exception as e:
        # If conversion fails, return original filepath
        return filepath

def get_available_weights():
    """Get list of available model weights"""
    weights = []
    
    # Check for pre-trained weights
    pretrained = BASE_DIR / 'yolov5s.pt'
    if pretrained.exists():
        weights.append({'name': 'YOLOv5s (Pre-trained)', 'path': str(pretrained)})
    
    # Check for custom trained weights
    custom_path = BASE_DIR / 'yolov5' / 'runs' / 'train'
    if custom_path.exists():
        for exp_dir in custom_path.iterdir():
            weights_file = exp_dir / 'weights' / 'best.pt'
            if weights_file.exists():
                weights.append({
                    'name': f'Custom Model ({exp_dir.name})',
                    'path': str(weights_file)
                })
    
    # Default yolov5s if no weights found
    if not weights:
        weights.append({'name': 'YOLOv5s (Default)', 'path': 'yolov5s.pt'})
    
    return weights

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/weights', methods=['GET'])
def get_weights():
    """Get available model weights"""
    weights = get_available_weights()
    return jsonify({'weights': weights})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Secure filename and add timestamp
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = filename.rsplit('.', 1)
        filename = f"{name}_{timestamp}.{ext}"
        
        # Save file
        filepath = app.config['UPLOAD_FOLDER'] / filename
        file.save(filepath)
        
        # Convert HEIF/HEIC files to PNG
        if is_image_file(filename):
            converted_path = convert_heif_to_png(filepath)
            if converted_path != filepath:
                # Update filename if converted
                filename = converted_path.name
                filepath = converted_path
        
        file_type = 'image' if is_image_file(filename) else 'video'
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': str(filepath),
            'type': file_type
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/detect', methods=['POST'])
def detect():
    """Run YOLOv5 detection on uploaded file"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        conf_thres = float(data.get('conf_thres', 0.4))
        weights_path = data.get('weights', 'yolov5s.pt')
        imgsz = int(data.get('imgsz', 640))
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        # Get file path
        filepath = app.config['UPLOAD_FOLDER'] / filename
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Determine if image or video
        is_image = is_image_file(filename)
        
        # Create unique result directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_dir = app.config['RESULTS_FOLDER'] / f"detect_{timestamp}"
        result_dir.mkdir(exist_ok=True)
        
        # Resolve weights path
        if not Path(weights_path).is_absolute():
            # Try relative paths
            if Path(weights_path).exists():
                weights_path = str(Path(weights_path).resolve())
            elif (BASE_DIR / weights_path).exists():
                weights_path = str((BASE_DIR / weights_path).resolve())
            else:
                # Use yolov5 default
                weights_path = str(BASE_DIR / 'yolov5' / weights_path)
        
        # Run YOLOv5 detection using subprocess
        try:
            yolov5_dir = BASE_DIR / 'yolov5'
            detect_script = yolov5_dir / 'detect.py'
            
            # Build command
            # Check if custom data.yaml exists for 2-class detection
            data_yaml = BASE_DIR / 'data_fish_notfish.yaml'
            cmd = [
                sys.executable,
                str(detect_script),
                '--weights', weights_path,
                '--source', str(filepath),
                '--img', str(imgsz),
                '--conf', str(conf_thres),
                '--project', str(result_dir),
                '--name', 'result',
                '--exist-ok',
                '--save-conf',
                '--save-txt',  # Save label files for parsing detections
                '--hide-labels'  # Hide COCO labels on image (we'll show Fish/notFish in UI)
            ]
            # Add data.yaml if it exists
            if data_yaml.exists():
                cmd.extend(['--data', str(data_yaml)])
            
            # Run detection
            result = subprocess.run(
                cmd,
                cwd=str(yolov5_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                # Provide more helpful error messages
                if 'Image Not Found' in error_msg:
                    return jsonify({
                        'error': f'Image file not readable. The file might be corrupted or in an unsupported format. Error: {error_msg[:300]}'
                    }), 500
                return jsonify({'error': f'Detection failed: {error_msg[:500]}'}), 500
                
        except subprocess.TimeoutExpired:
            return jsonify({'error': 'Detection timeout - file mungkin terlalu besar'}), 500
        except Exception as e:
            return jsonify({'error': f'Detection failed: {str(e)}'}), 500
        
        # Find result file
        result_file = None
        # YOLOv5 saves to: project/name/ (not project/name/result/)
        # So result_path should be result_dir itself when --name is used
        result_path = result_dir / 'result'
        # But YOLOv5 might save directly to result_dir if structure is different
        # Check both locations
        alt_result_path = result_dir
        
        # Get source image name (YOLOv5 uses original filename, not uploaded filename)
        source_image_name = Path(filepath).name
        
        if is_image:
            # For images, look for the processed image in both locations
            search_paths = [result_path, alt_result_path]
            for search_path in search_paths:
                for ext in ['.jpg', '.jpeg', '.png']:
                    base_name = source_image_name.rsplit('.', 1)[0]
                    test_file = search_path / f"{base_name}{ext}"
                    if test_file.exists():
                        result_file = test_file
                        break
                    test_file = search_path / source_image_name
                    if test_file.exists():
                        result_file = test_file
                        break
                if result_file:
                    break
            # Also check uploaded filename
            if not result_file:
                for search_path in [result_path, alt_result_path]:
                    for ext in ['.jpg', '.jpeg', '.png']:
                        base_name = filename.rsplit('.', 1)[0]
                        test_file = search_path / f"{base_name}{ext}"
                        if test_file.exists():
                            result_file = test_file
                            break
                    if result_file:
                        break
        else:
            # For videos, look for processed video
            for ext in ['.mp4', '.avi', '.mov']:
                base_name = source_image_name.rsplit('.', 1)[0]
                test_file = result_path / f"{base_name}{ext}"
                if test_file.exists():
                    result_file = test_file
                    break
                if not result_file and (result_path / source_image_name).exists():
                    result_file = result_path / source_image_name
        
        # Fallback: check if any file exists in result directories
        if not result_file:
            for search_path in [result_path, alt_result_path]:
                if search_path.exists():
                    files = list(search_path.glob('*'))
                    # Filter out directories
                    files = [f for f in files if f.is_file()]
                    if files:
                        result_file = files[0]
                        break
        
        if not result_file or not result_file.exists():
            return jsonify({'error': 'Result file not found after detection'}), 500
        
        # Get relative path for serving
        result_filename = result_file.name
        result_relative_path = f"detect_{timestamp}/result/{result_filename}"
        
        # Parse detection results if available
        # YOLOv5 saves labels with SOURCE filename, not uploaded filename!
        detections = []
        
        # Try multiple possible locations for label files
        # YOLOv5 structure: project/name/labels/source_filename.txt
        possible_label_paths = [
            result_path / 'labels' / (Path(source_image_name).stem + '.txt'),
            alt_result_path / 'labels' / (Path(source_image_name).stem + '.txt'),
            result_path / 'labels' / (Path(filename).stem + '.txt'),
            alt_result_path / 'labels' / (Path(filename).stem + '.txt'),
        ]
        
        txt_file = None
        for path in possible_label_paths:
            if path.exists():
                txt_file = path
                break
        
        # Check if we're using COCO model (yolov5s.pt) or custom fish model
        is_coco_model = 'yolov5s.pt' in str(weights_path).lower() or 'yolov5' in str(weights_path).lower()
        
        if txt_file.exists():
            # Parse YOLO format: class x_center y_center width height confidence
            with open(txt_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        confidence = float(parts[5]) if len(parts) > 5 else float(parts[4])
                        
                        if is_coco_model:
                            # Using COCO model - convert all to Fish (potential fish)
                            # All objects are considered potential fish
                            coco_class_name = COCO_CLASS_NAMES.get(class_id, f'class_{class_id}')
                            detections.append({
                                'class': 0,  # Map to Fish (potential fish)
                                'class_name': 'Fish',
                                'original_detection': coco_class_name,
                                'original_coco_id': class_id,
                                'confidence': confidence,
                                'bbox': [float(x) for x in parts[1:5]],
                                'is_coco': True
                            })
                        else:
                            # Using custom fish model
                            detections.append({
                                'class': class_id,
                                'class_name': CLASS_NAMES.get(class_id, f'Class_{class_id}'),
                                'confidence': confidence,
                                'bbox': [float(x) for x in parts[1:5]],
                                'is_coco': False
                            })
        
        return jsonify({
            'success': True,
            'result_file': result_filename,
            'result_path': result_relative_path,
            'type': 'image' if is_image else 'video',
            'detections': detections,
            'detection_count': len(detections),
            'model_type': 'coco' if is_coco_model else 'fish'
        })
    
    except Exception as e:
        import traceback
        return jsonify({'error': f'Server error: {str(e)}\n{traceback.format_exc()}'}), 500

@app.route('/api/results/<path:filename>')
def get_result(filename):
    """Serve result files"""
    # Security: only allow files from results folder
    result_path = app.config['RESULTS_FOLDER'] / filename
    if result_path.exists() and app.config['RESULTS_FOLDER'] in result_path.parents:
        return send_from_directory(str(result_path.parent), result_path.name)
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/uploads/<filename>')
def get_upload(filename):
    """Serve uploaded files"""
    filepath = app.config['UPLOAD_FOLDER'] / filename
    if filepath.exists():
        return send_from_directory(str(app.config['UPLOAD_FOLDER']), filename)
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'pytorch': torch.__version__,
        'cuda_available': torch.cuda.is_available()
    })

if __name__ == '__main__':
    import socket
    
    # Get port from environment variable (for production) or use default
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # For local development, find available port if default is in use
    if debug:
        def find_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]
        
        try:
            # Try the default port first
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
        except OSError:
            # Port in use, find another
            port = find_free_port()
            print(f"⚠️  Port sedang digunakan, menggunakan port {port}")
    
    print("🎣 Starting IKAN Fish Detection Web Interface...")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📁 Results folder: {app.config['RESULTS_FOLDER']}")
    print(f"🌐 Server running at http://0.0.0.0:{port}")
    app.run(debug=debug, host='0.0.0.0', port=port)
