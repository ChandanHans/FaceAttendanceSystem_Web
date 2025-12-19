"""
Laptop Camera Streaming Server
===============================
This server streams your laptop camera over HTTP so the Pi can access it.
Run this on your Windows laptop while the main app runs on the Pi.

Usage:
    python laptop_camera_server.py
    
The camera will be available at: http://YOUR_LAPTOP_IP:5001/video
"""

from flask import Flask, Response
from flask_cors import CORS
import cv2
import socket
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global camera object
camera = None

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket to find local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def init_camera():
    """Initialize the camera at startup"""
    global camera
    logging.info("🔍 Searching for available camera...")
    
    # Try different camera indices and backends
    for index in [0, 1, 2]:
        logging.info(f"Trying camera index {index}...")
        cam = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # Use DirectShow backend on Windows
        
        if cam.isOpened():
            # Test if we can actually read a frame
            ret, frame = cam.read()
            if ret:
                logging.info(f"✅ Camera {index} working! Resolution: {frame.shape[1]}x{frame.shape[0]}")
                
                # Set camera properties for better performance
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cam.set(cv2.CAP_PROP_FPS, 30)
                cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize lag
                
                camera = cam
                logging.info("✅ Camera initialized and ready!")
                return True
            else:
                logging.warning(f"Camera {index} opened but can't read frames")
                cam.release()
        else:
            logging.debug(f"Camera {index} not available")
    
    logging.error("❌ No working camera found!")
    return False

def get_camera():
    """Get the initialized camera"""
    return camera

def generate_frames():
    """Generate camera frames for streaming"""
    cam = get_camera()
    if cam is None or not cam.isOpened():
        logging.error("❌ Camera not available for streaming")
        # Send a simple error frame
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n'
               b'Camera not available\r\n')
        return
    
    frame_count = 0
    while True:
        success, frame = cam.read()
        if not success:
            logging.warning(f"Failed to read frame from camera (frame #{frame_count})")
            continue  # Try next frame instead of breaking
        
        frame_count += 1
        
        # Encode frame as JPEG with good quality
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ret:
            continue
        
        # Convert to bytes
        frame_bytes = buffer.tobytes()
        
        # Log progress periodically
        if frame_count % 100 == 0:
            logging.info(f"📹 Streamed {frame_count} frames")
        
        # Yield frame in multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    """Home page with information"""
    local_ip = get_local_ip()
    return f"""
    <html>
        <head>
            <title>Laptop Camera Server</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                }}
                .info {{
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .url {{
                    font-family: monospace;
                    background: #f5f5f5;
                    padding: 10px;
                    border-radius: 3px;
                    display: inline-block;
                    font-size: 14px;
                }}
                img {{
                    max-width: 100%;
                    border: 2px solid #ddd;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .status {{
                    color: #4CAF50;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📹 Laptop Camera Server</h1>
                <p class="status">✅ Server is running!</p>
                
                <div class="info">
                    <h3>Stream URL for Pi:</h3>
                    <p class="url">http://{local_ip}:5001/video</p>
                    <p>Use this URL in your Pi's config.json file.</p>
                </div>
                
                <h3>Live Camera Preview:</h3>
                <img src="/video" alt="Camera Stream">
                
                <div class="info">
                    <h3>Setup Instructions:</h3>
                    <ol>
                        <li>Keep this server running on your laptop</li>
                        <li>Make sure your laptop and Pi are on the same network</li>
                        <li>Update Pi's config.json with the URL above</li>
                        <li>Start your attendance system on the Pi</li>
                    </ol>
                </div>
            </div>
        </body>
    </html>
    """

@app.route('/video')
def video():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health():
    """Health check endpoint"""
    cam = get_camera()
    if cam and cam.isOpened():
        return {"status": "ok", "camera": "available"}, 200
    else:
        return {"status": "error", "camera": "unavailable"}, 503

def cleanup():
    """Cleanup resources"""
    global camera
    if camera is not None:
        camera.release()
        logging.info("Camera released")

if __name__ == '__main__':
    try:
        local_ip = get_local_ip()
        logging.info("=" * 60)
        logging.info("🎥 Laptop Camera Server Starting...")
        logging.info("=" * 60)
        logging.info(f"📍 Local IP: {local_ip}")
        logging.info(f"🌐 Access at: http://{local_ip}:5001")
        logging.info(f"📹 Stream URL: http://{local_ip}:5001/video")
        logging.info("=" * 60)
        
        # Initialize camera BEFORE starting server
        logging.info("\n🔄 Initializing camera...")
        if not init_camera():
            logging.error("\n❌ Failed to initialize camera. Please check:")
            logging.error("   1. Camera is not being used by another application")
            logging.error("   2. Camera permissions are granted")
            logging.error("   3. Camera drivers are installed")
            logging.info("\nServer will start anyway, but video won't work.\n")
        
        logging.info("\n💡 Keep this window open while using the camera!\n")
        
        # Run the server
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    except KeyboardInterrupt:
        logging.info("\n\n🛑 Server stopped by user")
    finally:
        cleanup()
