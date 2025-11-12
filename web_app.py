"""
Web-based GUI for Date Prefix Renamer
Flask application for Docker deployment
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from datetime import datetime
import shutil
import uuid

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Use /data directory if available (Docker), otherwise use user's Documents
base_dir = '/data' if os.path.exists('/data') else os.path.expanduser('~/Documents')
app.config['UPLOAD_FOLDER'] = base_dir
app.config['TEMP_UPLOAD_FOLDER'] = os.path.join(base_dir, '.uploads')

# Create temp upload folder if it doesn't exist
os.makedirs(app.config['TEMP_UPLOAD_FOLDER'], exist_ok=True)

# Store session data
sessions = {}

def get_file_date(file_path):
    """Get file creation or modification date"""
    try:
        stat_info = Path(file_path).stat()
        if hasattr(stat_info, 'st_birthtime'):
            return datetime.fromtimestamp(stat_info.st_birthtime)
        else:
            return datetime.fromtimestamp(stat_info.st_mtime)
    except Exception:
        return datetime.now()

def generate_preview(files):
    """Generate preview of rename operations"""
    preview = []
    
    for file_info in files:
        original_name = file_info['name']
        file_path = file_info['path']
        
        # Get file date
        file_date = get_file_date(file_path)
        date_prefix = file_date.strftime("%d%m%Y")
        
        # Generate new name
        new_name = f"{date_prefix}_{original_name}"
        
        preview.append({
            'original': original_name,
            'new': new_name,
            'date': file_date.strftime('%Y-%m-%d'),
            'path': file_path,
            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        })
    
    return preview

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads with folder structure support"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No files selected'}), 400
    
    # Create unique session upload folder
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(app.config['TEMP_UPLOAD_FOLDER'], session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    uploaded_files = []
    
    for file in files:
        if file.filename == '':
            continue
        
        try:
            # Use the full path from drag-drop to preserve folder structure
            file_path_rel = file.filename
            
            # Secure each path component but keep structure
            path_parts = []
            for part in file_path_rel.split('/'):
                if part:
                    safe_part = secure_filename(part)
                    if safe_part:
                        path_parts.append(safe_part)
            
            if not path_parts:
                continue
            
            # Reconstruct the relative path
            safe_rel_path = os.path.join(*path_parts)
            
            # Save to session folder
            filepath = os.path.join(session_folder, safe_rel_path)
            
            # Create subdirectories if needed
            directory = os.path.dirname(filepath)
            os.makedirs(directory, exist_ok=True)
            
            file.save(filepath)
            
            # Store with relative path for display
            uploaded_files.append({
                'name': safe_rel_path,
                'path': filepath
            })
            print(f"Uploaded: {safe_rel_path} -> {filepath}")
            
        except Exception as e:
            print(f"Error saving {file.filename}: {e}")
            continue
    
    if not uploaded_files:
        return jsonify({'error': 'No valid files uploaded'}), 400
    
    # Generate preview
    preview = generate_preview(uploaded_files)
    
    # Store session data
    sessions[session_id] = {
        'preview': preview,
        'files': uploaded_files,
        'session_folder': session_folder
    }
    
    print(f"Session {session_id}: {len(uploaded_files)} files uploaded")
    
    return jsonify({
        'session_id': session_id,
        'preview': preview,
        'count': len(preview)
    })

@app.route('/execute', methods=['POST'])
def execute_rename():
    """Execute the rename operation"""
    data = request.json
    session_id = data.get('session_id')
    
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session_data = sessions[session_id]
    preview = session_data['preview']
    session_folder = session_data.get('session_folder')
    results = []
    success_count = 0
    
    for item in preview:
        old_path = item['path']
        old_name = item['original']
        new_name = item['new']
        
        try:
            # Get the relative path to preserve folder structure
            if session_folder and old_path.startswith(session_folder):
                rel_path = os.path.relpath(old_path, session_folder)
                rel_dir = os.path.dirname(rel_path)
                
                # Determine final destination
                if rel_dir and rel_dir != '.':
                    # Keep folder structure
                    final_dir = os.path.join(app.config['UPLOAD_FOLDER'], rel_dir)
                else:
                    # Root level
                    final_dir = app.config['UPLOAD_FOLDER']
            else:
                # Fallback to original directory
                final_dir = os.path.dirname(old_path)
            
            # Create destination directory
            os.makedirs(final_dir, exist_ok=True)
            
            new_path = os.path.join(final_dir, new_name)
            
            # Check if target exists
            if os.path.exists(new_path):
                results.append({
                    'file': old_name,
                    'status': 'error',
                    'message': 'Target file already exists'
                })
                continue
            
            # Rename
            os.rename(old_path, new_path)
            success_count += 1
            
            results.append({
                'file': old_name,
                'status': 'success',
                'new_name': new_name
            })
            print(f"Renamed: {old_path} -> {new_path}")
            
        except Exception as e:
            print(f"Error renaming {old_name}: {e}")
            results.append({
                'file': old_name,
                'status': 'error',
                'message': str(e)
            })
    
    # Cleanup session and temp folder
    if session_folder and os.path.exists(session_folder):
        try:
            shutil.rmtree(session_folder)
            print(f"Cleaned up session folder: {session_folder}")
        except Exception as e:
            print(f"Error cleaning up {session_folder}: {e}")
    
    if session_id in sessions:
        del sessions[session_id]
    
    return jsonify({
        'success': success_count,
        'total': len(preview),
        'results': results
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Run on all interfaces for Docker
    app.run(host='0.0.0.0', port=8080, debug=False)
