"""
Central configuration file for application resources
This avoids duplication of initialization code between app.py and process_agents.py
"""
from flask import Flask
from flask_socketio import SocketIO
import logging
import tempfile
import os
from dotenv import load_dotenv

# Import the agent classes - circular import is avoided by importing inside the functions that use them
from agents.scout_agent import ScoutAgent
from agents.analyst_agent import AnalystAgent
from utils.text_processor import TextPreprocessor
from utils.mongodb_storage import MongoDBStorage

# Load environment variables from .env file
load_dotenv()

# =============================
# App Initialization
# =============================
# Get the project root directory (going up one level from utils)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, 
            template_folder=os.path.join(project_root, 'templates'),
            static_folder=os.path.join(project_root, 'static'))
            
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kollab_secret_key')
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
socketio = SocketIO(app, cors_allowed_origins="*")

# =============================
# Configuration Settings
# =============================
MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DB = os.environ.get('MONGODB_DB', 'KollabAgentic')

# =============================
# Logging Configuration
# =============================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================
# Text Preprocessor Initialization
# =============================
text_processor = TextPreprocessor()

# =============================
# Storage Initialization
# =============================
try:
    storage = MongoDBStorage(
        connection_string=MONGODB_URI,
        database_name=MONGODB_DB
    )
    logger.info(f"Connected to MongoDB")
except Exception as e:
    logger.warning(f"MongoDB connection failed: {str(e)}.")

# =============================
# Agent Initialization
# =============================
scout = ScoutAgent(socket_instance=socketio)
analyst = AnalystAgent(socket_instance=socketio)

# Print debug info about template and static paths
logger.info(f"Template directory: {app.template_folder}")
logger.info(f"Static directory: {app.static_folder}")