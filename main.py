from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import cv2
import time
import json
import os
import urllib.request
import traceback

from brainrot_eyedetection import EyeGazeTracker, BrainRotWarnings

app = Flask(__name__)
CORS(app) 

tracking_thread = None
tracker = None
is_tracking = False
session_stats = {}
error_message = ""

def tracking_worker(duration=None):
    """
    Background worker function that runs the eye tracking with improved error handling.
    
    Args:
        duration: Optional tracking duration in seconds
    """
    global is_tracking, tracker, session_stats, error_message
    
    try:
        tracker = EyeGazeTracker()
        
        cap = None
        for attempt in range(3):
            print(f"Attempting to open webcam (attempt {attempt+1}/3)")
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                print("Webcam opened successfully")
                break
            time.sleep(1)
        
        if not cap or not cap.isOpened():
            print("Error: Could not open webcam after multiple attempts")
            is_tracking = False
            error_message = "Could not access webcam after multiple attempts"
            session_stats = {"error": error_message}
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        start_time = time.time()
        
        # Auto-calibration
        print("Starting auto-calibration...")
        tracker.start_calibration()
        calibration_samples = 0
        
        consecutive_failures = 0
        max_failures = 10 
        
        # Main tracking loop
        while is_tracking:
            ret, frame = cap.read()
            
            if not ret:
                consecutive_failures += 1
                print(f"Failed to grab frame ({consecutive_failures}/{max_failures})")
                
                if consecutive_failures >= max_failures:
                    print("Too many consecutive frame failures, stopping tracking")
                    error_message = "Too many consecutive frame failures"
                    break
                
                # Wait a bit and try again
                time.sleep(0.5)
                continue
            
            # Reset failure counter on successful frame
            consecutive_failures = 0
            
            try:
                processed_frame = tracker.process_frame(frame)
                
                if tracker.calibration_active:
                    calibration_samples += 1
                    if calibration_samples >= 30:
                        print("Calibration completed")
            except Exception as e:
                print(f"Error processing frame: {e}")
                traceback.print_exc()
                continue
            
            if duration and time.time() - start_time > duration:
                print(f"Tracking duration of {duration} seconds completed")
                break
            
            # Small sleep to reduce CPU usage
            time.sleep(0.01)
        
        if tracker and tracker.brain_rot:
            if not tracker.brain_rot.is_focused and tracker.brain_rot.last_unfocus_time is not None:
                final_unfocused_duration = time.time() - tracker.brain_rot.last_unfocus_time
                tracker.brain_rot.not_focused_times += final_unfocused_duration
            
            total_seconds = tracker.brain_rot.not_focused_times
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            
            session_stats = {
                "times_looked_away": tracker.brain_rot.times_not_looking_at_screen,
                "total_unfocused_seconds": total_seconds,
                "total_unfocused_formatted": f"{minutes} min {seconds:.2f} sec",
                "session_duration": time.time() - start_time
            }
        
        # Clean up
        if cap:
            cap.release()
        print("Tracking stopped, stats collected")
        
    except Exception as e:
        print(f"Unexpected error in tracking thread: {e}")
        traceback.print_exc()
        error_message = f"Tracking error: {str(e)}"
        session_stats = {"error": error_message}
    
    finally:
        is_tracking = False
        if 'cap' in locals() and cap:
            cap.release()
        cv2.destroyAllWindows()

@app.route('/start', methods=['POST'])
def start_tracking():
    """Start eye tracking session."""
    global tracking_thread, is_tracking, session_stats, error_message
    
    if is_tracking:
        return jsonify({"status": "error", "message": "Tracking already in progress"})
    
    data = request.get_json(silent=True) or {}
    duration = data.get('duration') 
    
    if not os.path.exists('face_landmarker.task'):
        try:
            print("Downloading face landmarker model...")
            urllib.request.urlretrieve(
                'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
                'face_landmarker.task')
            print("Model downloaded successfully!")
        except Exception as e:
            error_msg = f"Failed to download model: {str(e)}"
            print(error_msg)
            return jsonify({"status": "error", "message": error_msg})
    
    session_stats = {}
    error_message = ""
    is_tracking = True
    
    tracking_thread = threading.Thread(target=tracking_worker, args=(duration,))
    tracking_thread.daemon = True
    tracking_thread.start()
    
    return jsonify({
        "status": "success", 
        "message": "Eye tracking started",
        "duration": duration
    })

@app.route('/stop', methods=['POST'])
def stop_tracking():
    """Stop eye tracking session."""
    global is_tracking
    
    if not is_tracking:
        return jsonify({"status": "error", "message": "No tracking in progress"})
    
    is_tracking = False
    
    wait_time = 0
    while tracking_thread and tracking_thread.is_alive() and wait_time < 3:
        time.sleep(0.1)
        wait_time += 0.1
    
    return jsonify({
        "status": "success",
        "message": "Eye tracking stopped",
        "stats": session_stats
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get current eye tracking statistics."""
    global tracker, is_tracking, session_stats, error_message
    
    if error_message:
        return jsonify({
            "status": "error",
            "message": error_message
        })
    
    if is_tracking and tracker and hasattr(tracker, 'brain_rot'):
        try:
            current_time = time.time()
            current_unfocused = tracker.brain_rot.not_focused_times
            
            if not tracker.brain_rot.is_focused and tracker.brain_rot.last_unfocus_time is not None:
                current_unfocused += current_time - tracker.brain_rot.last_unfocus_time
            
            total_seconds = current_unfocused
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            
            current_stats = {
                "status": "in_progress",
                "times_looked_away": tracker.brain_rot.times_not_looking_at_screen,
                "total_unfocused_seconds": total_seconds,
                "total_unfocused_formatted": f"{minutes} min {seconds:.2f} sec",
                "currently_focused": tracker.brain_rot.is_focused
            }
            return jsonify(current_stats)
        except Exception as e:
            print(f"Error getting real-time stats: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error getting stats: {str(e)}"
            })
    elif session_stats:
        return jsonify({**session_stats, "status": "completed"})
    else:
        return jsonify({
            "status": "not_started",
            "message": "No tracking session data available"
        })

@app.route('/status', methods=['GET'])
def get_status():
    """Get current tracking status."""
    global is_tracking, error_message
    
    status = "active" if is_tracking else "inactive"
    response = {"status": status}
    
    if error_message:
        response["error"] = error_message
    
    return jsonify(response)

@app.route('/reset_error', methods=['POST'])
def reset_error():
    """Reset any error message."""
    global error_message
    
    error_message = ""
    return jsonify({
        "status": "success",
        "message": "Error state reset"
    })

@app.route('/', methods=['GET'])
def home():
    """Simple home page to verify server is running."""
    return jsonify({
        "status": "running",
        "message": "Eye tracking server is running.",
        "endpoints": [
            {"url": "/start", "method": "POST", "description": "Start eye tracking"},
            {"url": "/stop", "method": "POST", "description": "Stop eye tracking"},
            {"url": "/stats", "method": "GET", "description": "Get tracking statistics"},
            {"url": "/status", "method": "GET", "description": "Check tracking status"},
            {"url": "/reset_error", "method": "POST", "description": "Reset error state"}
        ]
    })

if __name__ == '__main__':
    print("Starting Eye Tracking Server on http://localhost:6363")
    app.run(host='0.0.0.0', port=6363, debug=True)