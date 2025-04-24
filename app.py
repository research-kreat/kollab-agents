from flask import Flask, request, jsonify, render_template, session
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
import os
import json
import logging
import time
import uuid
import tempfile
from agents.scout_agent import ScoutAgent
from agents.analyst_agent import AnalystAgent
from agents.orchestrator_agent import OrchestratorAgent
from utils.file_processor import process_file

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kollab_secret_key'
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize agents with SocketIO
scout = ScoutAgent(socket_instance=socketio)
analyst = AnalystAgent(socket_instance=socketio)
orchestrator = OrchestratorAgent(socket_instance=socketio)

# In-memory storage for current session data
current_uploads = {}

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    socketio.emit('status', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Generate a unique ID for this upload
    upload_id = str(uuid.uuid4())
    
    # Secure the filename
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Save the file temporarily
    file.save(file_path)
    
    try:
        # Process the file to extract content
        socketio.emit('status', {'message': 'Processing file...'})
        content, file_type = process_file(file_path)
        
        # Store the processed content with the upload ID
        current_uploads[upload_id] = {
            'file_path': file_path,
            'content': content,
            'file_type': file_type,
            'timestamp': time.time()
        }
        
        socketio.emit('status', {'message': 'File processed successfully'})
        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'message': 'File processed successfully',
            'file_type': file_type,
            'record_count': len(content) if isinstance(content, list) else 1
        })
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        socketio.emit('status', {'message': f'Error: {str(e)}'})
        
        # Clean up the file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_data():
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    upload_id = data.get('upload_id')
    query = data.get('query')
    
    if not upload_id or not query:
        return jsonify({'error': 'Missing upload_id or query parameter'}), 400
    
    if upload_id not in current_uploads:
        return jsonify({'error': 'Invalid upload ID or session expired'}), 400
    
    try:
        socketio.emit('status', {'message': 'Starting analysis...'})
        
        # Get the uploaded content
        upload_data = current_uploads[upload_id]
        content = upload_data['content']
        
        # Create a process ID for tracking
        process_id = str(uuid.uuid4())
        
        # Run the analysis through our CrewAI agents
        socketio.emit('status', {'message': 'Scout agent processing data...'})
        scout_results = scout.process_scout_query({
            'content': content,
            'query': query,
            'process_id': process_id
        })

        print("[scout_results_JSON]",scout_results)
        
        socketio.emit('status', {'message': 'Analyst agent reviewing findings...'})
        analyst_results = analyst.process_analyst_query(scout_results)

        print("[analyst_results_JSON]",analyst_results)
        
        socketio.emit('status', {'message': 'Orchestrating final results...'})
        final_results = orchestrator.orchestrate_analysis(analyst_results, query)

        print("[final_results_JSON]",final_results)
        
        # Clean up the temporary file
        if os.path.exists(upload_data['file_path']):
            os.remove(upload_data['file_path'])
        
        # Remove from memory
        del current_uploads[upload_id]
        
        socketio.emit('status', {'message': 'Analysis complete'})
        return jsonify(final_results)
        
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        socketio.emit('status', {'message': f'Error: {str(e)}'})
        return jsonify({'error': str(e)}), 500

# Cleanup function to run periodically (could be triggered by a background task)
def cleanup_old_uploads():
    current_time = time.time()
    expired_uploads = []
    
    # Find uploads older than 1 hour
    for upload_id, data in current_uploads.items():
        if current_time - data['timestamp'] > 3600:  # 1 hour
            expired_uploads.append(upload_id)
            
            # Clean up file
            if os.path.exists(data['file_path']):
                os.remove(data['file_path'])
    
    # Remove expired uploads from memory
    for upload_id in expired_uploads:
        del current_uploads[upload_id]
    
    logger.info(f"Cleaned up {len(expired_uploads)} expired uploads")

# Error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large (max 16MB)'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Kollab server...")
    socketio.run(app, debug=True, host='0.0.0.0', allow_unsafe_werkzeug=True)