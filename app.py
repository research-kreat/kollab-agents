# =============================
# Imports
# =============================
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
import os
import json
import logging
import time
import uuid
import tempfile
from datetime import datetime

# Custom modules
from agents.scout_agent import ScoutAgent
from agents.analyst_agent import AnalystAgent
from utils.file_processor import process_file
from utils.storage import StorageManager

# =============================
# App Initialization
# =============================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kollab_secret_key')
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
socketio = SocketIO(app, cors_allowed_origins="*")

# =============================
# Logging Configuration
# =============================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================
# Agent & Storage Initialization
# =============================
storage = StorageManager()
scout = ScoutAgent(socket_instance=socketio)
analyst = AnalystAgent(socket_instance=socketio)
current_uploads = {}  

# =============================
# Template Filters
# =============================
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """Convert Unix timestamp to readable date"""
    if not timestamp:
        return "Unknown date"
    return datetime.fromtimestamp(timestamp).strftime('%B %d, %Y %H:%M')

# =============================
# Socket.IO Event Handlers
# =============================
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    socketio.emit('status', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

# =============================
# Routes
# =============================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard/<company_id>')
def dashboard(company_id):
    """Display company dashboard with all analyses"""
    result = storage.get_all_analyses(company_id)
    
    if not result['success']:
        return render_template('error.html', message=result['error'])
    
    analyses = result['data']
    status_counts = {'new': 0, 'processing': 0, 'resolved': 0, 'failed': 0}
    
    for analysis in analyses:
        status = analysis.get('status', 'new')
        if status in status_counts:
            status_counts[status] += 1
    
    return render_template(
        'dashboard.html',
        company_name=company_id.replace('_', ' ').title(),
        company_id=company_id,
        analyses=analyses,
        status_counts=status_counts
    )

# =============================
# API Endpoints
# =============================
@app.route('/api/analyze', methods=['POST'])
def upload_and_analyze():
    """Combined endpoint to upload and analyze file in a single operation"""
    # Check if file exists in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get the other parameters from the form data
    company_id = request.form.get('company_id', 'default_company')
    query = request.form.get('query', 'What are the key issues and actionable insights from this feedback?')
    save_analysis = request.form.get('save_analysis', 'true').lower() == 'true'
    
    # Generate process ID
    process_id = str(uuid.uuid4())
    
    try:
        # Step 1: Upload and process the file
        socketio.emit('status', {'message': 'Processing file...'})
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the file
        content, file_type = process_file(file_path)
        socketio.emit('status', {'message': f'File processed successfully. Found {len(content) if isinstance(content, list) else 1} records.'})
        
        # Step 2: Scout agent processing
        socketio.emit('status', {'message': 'Scout agent processing data...'})
        scout_results = scout.process_scout_query({
            'content': content,
            'query': query,
            'process_id': process_id,
            'company_id': company_id
        })

        if 'error' in scout_results:
            socketio.emit('status', {'message': f'Error in Scout analysis: {scout_results["error"]}'})
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify(scout_results), 500
        
        # Step 3: Analyst agent processing
        socketio.emit('status', {'message': 'Analyst agent reviewing findings...'})
        final_results = analyst.process_analyst_query(scout_results)
        
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Initialize status for each issue
        if 'final_report' in final_results and 'issues' in final_results['final_report']:
            for issue in final_results['final_report']['issues']:
                issue['status'] = 'new'
        
        # Step 4: Save analysis if requested
        if save_analysis:
            save_result = storage.save_analysis(final_results, company_id)
            final_results['saved'] = save_result['success']
            if save_result['success']:
                final_results['ticket_id'] = save_result['ticket_id']
            else:
                logger.error(f"Failed to save analysis: {save_result['error']}")
        
        socketio.emit('status', {'message': 'Analysis complete'})
        return jsonify(final_results)
        
    except Exception as e:
        logger.error(f"Error processing and analyzing file: {str(e)}")
        socketio.emit('status', {'message': f'Error: {str(e)}'})
        # Clean up temporary file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/<company_id>/<ticket_id>')
def get_analysis(company_id, ticket_id):
    """Fetch specific analysis record"""
    result = storage.get_analysis(company_id, ticket_id)
    if result['success']:
        return jsonify(result)
    return jsonify({'success': False, 'error': result['error']}), 404

@app.route('/api/task/status', methods=['POST'])
def update_task_status():
    """Update status of a specific task"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    company_id = data.get('company_id')
    ticket_id = data.get('ticket_id')
    task_index = data.get('task_index')
    new_status = data.get('status')
    
    if not all([company_id, ticket_id, new_status]) or task_index is None:
        return jsonify({'error': 'Missing required parameters'}), 400
        
    result = storage.update_task_status(company_id, ticket_id, task_index, new_status)
    if result['success']:
        return jsonify(result)
    return jsonify({'success': False, 'error': result['error']}), 500

# =============================
# Helpers
# =============================
def cleanup_old_uploads():
    """Remove old uploads older than 1 hour"""
    current_time = time.time()
    expired_uploads = []

    for upload_id, data in current_uploads.items():
        if current_time - data['timestamp'] > 3600:
            expired_uploads.append(upload_id)
            if os.path.exists(data['file_path']):
                os.remove(data['file_path'])

    for upload_id in expired_uploads:
        del current_uploads[upload_id]
    
    logger.info(f"Cleaned up {len(expired_uploads)} expired uploads")

# =============================
# Error Handlers
# =============================
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large (max 16MB)'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', message='Page not found'), 404

# =============================
# Main Entry Point
# =============================
if __name__ == '__main__':
    logger.info("Starting Kollab server...")
    socketio.run(app, debug=True, host='0.0.0.0', allow_unsafe_werkzeug=True)