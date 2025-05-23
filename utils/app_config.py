"""
Central configuration file for application resources
This avoids duplication of initialization code between app.py and process_agents.py
"""
from flask import Flask
from flask_socketio import SocketIO
import logging
import tempfile
import os

# Import the agent classes - circular import is avoided by importing inside the functions that use them
from agents.scout_agent import ScoutAgent
from agents.analyst_agent import AnalystAgent
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