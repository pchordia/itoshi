#!/usr/bin/env python3
"""
Web Application: Interactive Anime Video Generator
User uploads a selfie, describes what they want, and gets an anime video
"""

import os
import sys
import uuid
import json
import shutil
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, session
from werkzeug.utils import secure_filename
import threading
import queue

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from interactive_prompt_builder import InteractivePromptBuilder
import subprocess

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs/web'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Store active sessions
sessions = {}

class SessionData:
    def __init__(self, session_id):
        self.session_id = session_id
        self.builder = InteractivePromptBuilder(max_questions=5)
        self.uploaded_image = None
        self.prompts = None
        self.activity_name = None
        self.generated_image = None
        self.generated_video = None
        self.status = "awaiting_input"  # awaiting_input, generating_prompts, running_i2i, running_i2v, complete, error
        self.error = None
        self.log = []
    
    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {message}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_session_data(session_id):
    if session_id not in sessions:
        sessions[session_id] = SessionData(session_id)
    return sessions[session_id]

@app.route('/')
def index():
    """Serve the main page"""
    # Create new session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_conversation():
    """Start the interactive prompt generation"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session'}), 400
    
    data = request.json
    user_input = data.get('message', '').strip()
    
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    
    sess_data = get_session_data(session_id)
    sess_data.add_log(f"User: {user_input}")
    sess_data.status = "generating_prompts"
    
    try:
        response, response_time = sess_data.builder.start_conversation(user_input)
        sess_data.add_log(f"Assistant ({response_time:.2f}s): {response}")
        
        return jsonify({
            'response': response,
            'response_time': response_time,
            'questions_remaining': sess_data.builder.get_questions_remaining(),
            'status': sess_data.status
        })
    except Exception as e:
        sess_data.status = "error"
        sess_data.error = str(e)
        sess_data.add_log(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/message', methods=['POST'])
def send_message():
    """Send a message in the conversation"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session'}), 400
    
    data = request.json
    user_input = data.get('message', '').strip()
    
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    
    sess_data = get_session_data(session_id)
    sess_data.add_log(f"User: {user_input}")
    
    try:
        response, prompts, response_time = sess_data.builder.send_message(user_input)
        
        if prompts:
            # Prompts generated!
            sess_data.prompts = prompts
            sess_data.activity_name = prompts.get("activity_name", "custom_scene")
            sess_data.status = "prompts_ready"
            sess_data.add_log(f"✅ Prompts generated in {response_time:.2f}s")
            
            return jsonify({
                'prompts_generated': True,
                'prompts': prompts,
                'activity_name': sess_data.activity_name,
                'response_time': response_time,
                'status': sess_data.status
            })
        else:
            sess_data.add_log(f"Assistant ({response_time:.2f}s): {response}")
            
            return jsonify({
                'response': response,
                'response_time': response_time,
                'questions_remaining': sess_data.builder.get_questions_remaining(),
                'prompts_generated': False,
                'status': sess_data.status
            })
    except Exception as e:
        sess_data.status = "error"
        sess_data.error = str(e)
        sess_data.add_log(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Upload a selfie image"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session'}), 400
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        sess_data = get_session_data(session_id)
        
        # Create upload directory for this session
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        sess_data.uploaded_image = filepath
        sess_data.add_log(f"📸 Uploaded: {filename}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'Image uploaded successfully'
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/generate', methods=['POST'])
def generate_video():
    """Run the full pipeline: i2i + i2v"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session'}), 400
    
    sess_data = get_session_data(session_id)
    
    if not sess_data.uploaded_image:
        return jsonify({'error': 'No image uploaded'}), 400
    
    if not sess_data.prompts:
        return jsonify({'error': 'No prompts generated'}), 400
    
    # Run generation in background thread
    thread = threading.Thread(target=run_generation, args=(sess_data,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Generation started'
    })

def run_generation(sess_data):
    """Run i2i and i2v generation (background thread)"""
    try:
        activity_name = sess_data.activity_name
        prompts = sess_data.prompts
        
        # Save prompts to temporary files
        temp_dir = f"temp_web_{sess_data.session_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        i2i_prompts_file = os.path.join(temp_dir, "i2i_prompt.txt")
        i2v_prompts_file = os.path.join(temp_dir, "i2v_prompt.txt")
        
        with open(i2i_prompts_file, "w", encoding="utf-8") as f:
            f.write(f"{activity_name}: {prompts['i2i_prompt']}")
        
        with open(i2v_prompts_file, "w", encoding="utf-8") as f:
            f.write(f"{activity_name}: {prompts['i2v_prompt']}")
        
        # Create temp input directory
        temp_input_dir = os.path.join(temp_dir, "input")
        os.makedirs(temp_input_dir, exist_ok=True)
        
        # Copy uploaded image
        image_name = Path(sess_data.uploaded_image).name
        temp_image = os.path.join(temp_input_dir, image_name)
        shutil.copy2(sess_data.uploaded_image, temp_image)
        
        # Run i2i
        sess_data.status = "running_i2i"
        sess_data.add_log("🎨 Running i2i (anime conversion)...")
        
        i2i_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], sess_data.session_id, "images")
        os.makedirs(i2i_output_dir, exist_ok=True)
        
        cmd = [
            "python", "src/batch_media.py", "anime",
            "--input", temp_input_dir,
            "--output", i2i_output_dir,
            "--prompts", i2i_prompts_file,
            "--prompt-name", activity_name,
            "--workers", "1"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"i2i failed: {result.stderr}")
        
        # Find generated image
        output_path = Path(i2i_output_dir)
        latest_dir = max(output_path.glob("*/"), key=os.path.getmtime)
        generated_images = list(latest_dir.glob("*.png"))
        
        if not generated_images:
            raise RuntimeError("No generated images found")
        
        sess_data.generated_image = str(generated_images[0])
        sess_data.add_log(f"✅ i2i complete: {Path(sess_data.generated_image).name}")
        
        # Prepare for i2v
        temp_i2v_input_dir = os.path.join(temp_dir, "i2v_input")
        os.makedirs(temp_i2v_input_dir, exist_ok=True)
        shutil.copy2(sess_data.generated_image, os.path.join(temp_i2v_input_dir, Path(sess_data.generated_image).name))
        
        # Run i2v
        sess_data.status = "running_i2v"
        sess_data.add_log("🎬 Running i2v (video generation)...")
        
        i2v_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], sess_data.session_id, "videos")
        os.makedirs(i2v_output_dir, exist_ok=True)
        
        cmd = [
            "python", "src/batch_media.py", "i2v",
            "--input", temp_i2v_input_dir,
            "--output", i2v_output_dir,
            "--prompts", i2v_prompts_file,
            "--prompt-name", activity_name,
            "--workers", "1",
            "--duration", "5"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"i2v failed: {result.stderr}")
        
        # Find generated video
        output_path = Path(i2v_output_dir)
        latest_dir = max(output_path.glob("*/"), key=os.path.getmtime)
        generated_videos = list(latest_dir.glob("*.mp4"))
        
        if not generated_videos:
            raise RuntimeError("No generated videos found")
        
        sess_data.generated_video = str(generated_videos[0])
        sess_data.add_log(f"✅ i2v complete: {Path(sess_data.generated_video).name}")
        
        sess_data.status = "complete"
        sess_data.add_log("🎉 Generation complete!")
        
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        sess_data.status = "error"
        sess_data.error = str(e)
        sess_data.add_log(f"❌ Error: {e}")

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current session status"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session'}), 400
    
    sess_data = get_session_data(session_id)
    
    response = {
        'status': sess_data.status,
        'log': sess_data.log,
        'has_image': sess_data.uploaded_image is not None,
        'has_prompts': sess_data.prompts is not None,
        'error': sess_data.error
    }
    
    if sess_data.generated_image:
        # Make path relative for web serving
        rel_path = os.path.relpath(sess_data.generated_image, app.config['OUTPUT_FOLDER'])
        response['generated_image'] = f"/outputs/{rel_path}"
    
    if sess_data.generated_video:
        rel_path = os.path.relpath(sess_data.generated_video, app.config['OUTPUT_FOLDER'])
        response['generated_video'] = f"/outputs/{rel_path}"
    
    return jsonify(response)

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    """Serve generated files"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/api/reset', methods=['POST'])
def reset_session():
    """Reset the current session"""
    session_id = session.get('session_id')
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    # Create new session
    session['session_id'] = str(uuid.uuid4())
    
    return jsonify({'success': True, 'session_id': session['session_id']})

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Get port from environment (for Railway, Render, Heroku, etc.) or default to 5001
    port = int(os.environ.get('PORT', 5001))
    
    print("=" * 70)
    print("🎬 Interactive Anime Video Generator - Web App")
    print("=" * 70)
    print("")
    print(f"Starting server on http://localhost:{port}")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    
    # Check if running in production (has PORT env var) or development
    debug_mode = os.environ.get('PORT') is None
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port, threaded=True)

