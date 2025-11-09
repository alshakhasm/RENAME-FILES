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
import tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

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
    """Handle file uploads"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_files = []
    
    for file in files:
        if file.filename == '':
            continue
        
        filename = secure_filename(file.filename)
        if not filename:
            continue
            
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            uploaded_files.append({
                'name': filename,
                'path': filepath
            })
        except Exception as e:
            print(f"Error saving {filename}: {e}")
            continue
    
    if not uploaded_files:
        return jsonify({'error': 'No valid files uploaded'}), 400
    
    # Generate preview
    preview = generate_preview(uploaded_files)
    
    # Store in session
    session_id = str(hash(tuple(f['path'] for f in uploaded_files)))
    sessions[session_id] = {
        'preview': preview,
        'files': uploaded_files
    }
    
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
    results = []
    success_count = 0
    
    for item in preview:
        old_path = item['path']
        old_name = item['original']
        new_name = item['new']
        
        try:
            # Get directory
            directory = os.path.dirname(old_path)
            new_path = os.path.join(directory, new_name)
            
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
            
        except Exception as e:
            results.append({
                'file': old_name,
                'status': 'error',
                'message': str(e)
            })
    
    # Cleanup session
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
