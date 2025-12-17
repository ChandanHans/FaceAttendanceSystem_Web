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
import cv2
import socket
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

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

def get_camera():
    """Get or initialize the camera"""
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)  # Use default laptop camera
        if not camera.isOpened():
            logging.error("Failed to open camera!")
            return None
        # Set camera properties for better performance
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        logging.info("Camera initialized successfully")
    return camera

def generate_frames():
    """Generate camera frames for streaming"""
    cam = get_camera()
    if cam is None:
        logging.error("Camera not available")
        return
    
    while True:
        success, frame = cam.read()
        if not success:
            logging.warning("Failed to read frame from camera")
            break
        else:
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
            
            # Convert to bytes
            frame_bytes = buffer.tobytes()
            
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
        logging.info("\n💡 Keep this window open while using the camera!\n")
        
        # Run the server
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    except KeyboardInterrupt:
        logging.info("\n\n🛑 Server stopped by user")
    finally:
        cleanup()
