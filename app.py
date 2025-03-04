import os
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory
import logging
from dotenv import load_dotenv
from qr_extractor import extract_qr_code, decode_qr_content

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configuration from environment variables
SCHOOL_URL = os.environ.get('SCHOOL_URL', 'https://qehsn.ha.org.hk')
USERNAME = os.environ.get('USERNAME', '')
PASSWORD = os.environ.get('PASSWORD', '')
INTERVAL_MINUTES = int(os.environ.get('INTERVAL_MINUTES', 30))
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', 'qr_codes')

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Store the latest QR code information
latest_qr_info = {
    'path': None,
    'timestamp': None,
    'content': None
}

def background_extraction():
    """
    Background thread function to periodically extract QR codes
    """
    global latest_qr_info
    
    logger.info(f"Starting background QR extraction thread. Checking every {INTERVAL_MINUTES} minutes.")
    
    while True:
        try:
            logger.info(f"Attempting QR extraction at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Set up login credentials if provided
            login_credentials = None
            if USERNAME and PASSWORD:
                login_credentials = (USERNAME, PASSWORD)
                logger.info("Using provided login credentials")
            
            # Extract QR codes
            qr_paths = extract_qr_code(SCHOOL_URL, login_credentials, OUTPUT_DIR)
            
            if qr_paths and len(qr_paths) > 0:
                # Get the most recent QR code
                latest_qr = qr_paths[0]
                
                # Try to decode QR content
                qr_content = decode_qr_content(latest_qr)
                
                # Update latest QR info
                latest_qr_info = {
                    'path': os.path.basename(latest_qr),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'content': qr_content
                }
                
                logger.info(f"Updated latest QR code: {latest_qr_info['path']}")
            else:
                logger.warning("No QR codes were extracted in this cycle")
                
        except Exception as e:
            logger.error(f"Error in extraction cycle: {str(e)}")
        
        # Wait for next interval
        logger.info(f"Waiting {INTERVAL_MINUTES} minutes until next extraction...")
        time.sleep(INTERVAL_MINUTES * 60)

# Routes
@app.route('/')
def index():
    """Home page showing the latest QR code"""
    return render_template('index.html', qr_info=latest_qr_info)

@app.route('/api/latest')
def api_latest():
    """API endpoint to get latest QR info"""
    return jsonify(latest_qr_info)

@app.route('/qr_codes/<path:filename>')
def serve_qr_code(filename):
    """Serve QR code images"""
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    # Create and start the background extraction thread
    extraction_thread = threading.Thread(target=background_extraction, daemon=True)
    extraction_thread.start()
    
    # Start the Flask web server
    app.run(host='0.0.0.0', port=8080)
