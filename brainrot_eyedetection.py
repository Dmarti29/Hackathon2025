import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import math
import time
import requests
import json
from datetime import datetime

class BrainRotWarnings:
    """
    Tracks metrics for time spent not looking at screen.
    """
    def __init__(self, backend_url="http://localhost:5001", user_id="test_user", trigger_threshold=1, look_away_duration=5):
        """
        Initialize brain rot warning tracker.
        
        Args:
            backend_url: URL of the Flask backend
            user_id: ID of the current user
            trigger_threshold: Number of look-away events before triggering brain rot alert
            look_away_duration: Duration in seconds that counts as a single look-away event
        """
        self.not_focused_times = 0.0  # Total time spent not looking at screen
        self.times_not_looking_at_screen = 0  # Count of distinct look-away events
        self.is_focused = True  # Current focus state
        self.last_unfocus_time = None  # Timestamp when user last looked away
        self.current_unfocus_duration = 0.0  # Duration of current unfocus period
        
        # Backend integration
        self.backend_url = backend_url
        self.user_id = user_id
        self.trigger_threshold = trigger_threshold
        self.look_away_duration = look_away_duration  # Duration in seconds that counts as a look-away event
        self.triggered = False  # Flag to track if brain rot has been triggered in this session
        self.last_event_time = 0  # Time of last look-away event
    
    def not_focused(self, focused):
        """
        Update focus tracking metrics.
        
        @param focused: Boolean indicating if user is currently looking at screen
        """
        current_time = time.perf_counter()
        
        if not self.is_focused and focused:
            # User just looked back at the screen after looking away
            if self.last_unfocus_time is not None:
                unfocused_duration = current_time - self.last_unfocus_time
                self.not_focused_times += unfocused_duration
                
                # If the user was looking away for at least look_away_duration seconds,
                # count it as a look-away event
                if unfocused_duration >= self.look_away_duration:
                    self.times_not_looking_at_screen += 1
                    print(f"Look-away event {self.times_not_looking_at_screen}/{self.trigger_threshold} detected! Duration: {unfocused_duration:.1f}s")
                    self.last_event_time = current_time
                    
                    # Check if we've reached the trigger threshold
                    if self.times_not_looking_at_screen >= self.trigger_threshold and not self.triggered:
                        self.trigger_brainrot_alert()
                
                self.last_unfocus_time = None
            self.is_focused = True
        
        elif self.is_focused and not focused:
            # User just looked away from the screen
            self.last_unfocus_time = current_time
            self.is_focused = False
                
    def trigger_brainrot_alert(self):
        """
        Send a brain rot alert to the backend
        """
        try:
            # Prepare the payload
            payload = {
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "look_away_count": self.times_not_looking_at_screen,
                "notes": f"User looked away {self.times_not_looking_at_screen} times"
            }
            
            # Send the request
            response = requests.post(
                f"{self.backend_url}/api/brainrot/trigger",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                print(f"✅ Brain rot alert triggered: {response.json()}")
                self.times_not_looking_at_screen = 0  # Reset counter
            else:
                print(f"❌ Failed to trigger brain rot alert: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error triggering brain rot alert: {e}")
        
        
            
    def reset_trigger(self):
        """
        Reset the trigger flag to allow new brain rot detection
        """
        self.triggered = False
        self.times_not_looking_at_screen = 0
        print("Brain rot detection reset - starting fresh count")


class EyeGazeTracker:
    """
    Eye gaze tracking implementation using MediaPipe Face Landmarker.
    Detects if a user is looking at the screen based on eye and iris positions.
    """
    def __init__(self, model_path="face_landmarker.task", backend_url="http://localhost:5001", user_id="test_user"):
        """
        Initialize the eye gaze tracker.
        
        @param model_path: Path to the MediaPipe face landmarker model file
        """
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)
        
        self.LEFT_EYE_OUTLINE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.RIGHT_EYE_OUTLINE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        
        self.LEFT_IRIS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS = [473, 474, 475, 476, 477]
        
        self.LEFT_EYE_TOP_BOTTOM = [386, 374]
        self.RIGHT_EYE_TOP_BOTTOM = [159, 145]
        
        self.LEFT_EYE_LEFT_RIGHT = [263, 362]
        self.RIGHT_EYE_LEFT_RIGHT = [133, 33]
        
        self.LEFT_EYE_VERTICAL = [(386, 374), (385, 380), (387, 373)]
        self.RIGHT_EYE_VERTICAL = [(159, 145), (158, 153), (160, 144)]
        self.LEFT_EYE_HORIZONTAL = [(263, 362)]
        self.RIGHT_EYE_HORIZONTAL = [(133, 33)]
        
        self.screen_attention_history = [False] * 5
        self.looking_at_screen = False
        
        self.gaze_ratio_center_x = 0.0
        self.gaze_ratio_center_y = 0.0
        self.gaze_threshold_x = 0.18
        self.gaze_threshold_y = 0.12
        
        self.calibration_active = False
        self.calibration_samples = []
        self.calibration_complete = False
        
        self.show_mesh = True
        self.show_eyes_only = True
        self.debug_level = 1
        
        self.use_head_pose_compensation = True

        self.prev_frame_time = 0
        # Initialize brain rot tracking
        self.brain_rot = BrainRotWarnings(backend_url=backend_url, user_id=user_id)

    def calculate_ear(self, landmarks, vertical_indices, horizontal_indices):
        """
        Calculate Eye Aspect Ratio (EAR) which indicates eye openness.
        
        @param landmarks: Array of facial landmark points
        @param vertical_indices: List of index pairs for vertical eye measurements
        @param horizontal_indices: List of index pairs for horizontal eye measurements
        @return: Eye aspect ratio value
        """
        v_dists = []
        for p1_idx, p2_idx in vertical_indices:
            p1 = landmarks[p1_idx]
            p2 = landmarks[p2_idx]
            dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            v_dists.append(dist)
        
        h_dists = []
        for p1_idx, p2_idx in horizontal_indices:
            p1 = landmarks[p1_idx]
            p2 = landmarks[p2_idx]
            dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            h_dists.append(dist)
        
        if not h_dists or sum(h_dists) == 0:
            return 0
            
        return sum(v_dists) / len(v_dists) / (sum(h_dists) / len(h_dists))

    def get_landmarks_array(self, face_landmarks, image_shape):
        """
        Convert normalized landmarks to pixel coordinates.
        
        @param face_landmarks: MediaPipe normalized face landmarks
        @param image_shape: Shape of the image (height, width)
        @return: Array of landmark points in pixel coordinates
        """
        height, width = image_shape[:2]
        landmarks_array = []
        
        for landmark in face_landmarks:
            landmarks_array.append([
                landmark.x * width,
                landmark.y * height,
                landmark.z
            ])
            
        return landmarks_array

    def calculate_gaze_ratio(self, landmarks, eye_indices, iris_indices):
        """
        Calculate the iris position relative to the eye center.
        
        @param landmarks: Array of facial landmark points
        @param eye_indices: Indices for eye outline landmarks
        @param iris_indices: Indices for iris landmarks
        @return: Tuple containing x_ratio, y_ratio, eye_center coordinates, and iris_center coordinates
        """
        eye_xs = [landmarks[idx][0] for idx in eye_indices]
        eye_ys = [landmarks[idx][1] for idx in eye_indices]
        eye_center_x = sum(eye_xs) / len(eye_xs)
        eye_center_y = sum(eye_ys) / len(eye_ys)
        
        iris_xs = [landmarks[idx][0] for idx in iris_indices]
        iris_ys = [landmarks[idx][1] for idx in iris_indices]
        iris_center_x = sum(iris_xs) / len(iris_xs)
        iris_center_y = sum(iris_ys) / len(iris_ys)
        
        eye_width = max(eye_xs) - min(eye_xs)
        eye_height = max(eye_ys) - min(eye_ys)
        
        if eye_width == 0 or eye_height == 0:
            return 0, 0
        
        x_ratio = (iris_center_x - eye_center_x) / (eye_width * 0.5)
        y_ratio = (iris_center_y - eye_center_y) / (eye_height * 0.5)
        
        return x_ratio, y_ratio, (eye_center_x, eye_center_y), (iris_center_x, iris_center_y)

    def is_looking_at_screen(self, left_gaze, right_gaze, left_ear, right_ear):
        """
        Determine if the user is looking at the screen based on eye and iris positions.
        
        @param left_gaze: Tuple of (x_ratio, y_ratio) for left eye
        @param right_gaze: Tuple of (x_ratio, y_ratio) for right eye
        @param left_ear: Left eye aspect ratio (openness)
        @param right_ear: Right eye aspect ratio (openness)
        @return: Boolean indicating if user is looking at screen
        """
        min_ear_threshold = 0.11
        
        if left_ear < min_ear_threshold and right_ear < min_ear_threshold:
            return False
        
        gaze_x_values = []
        gaze_y_values = []
        
        if left_ear >= min_ear_threshold:
            gaze_x_values.append(left_gaze[0])
            gaze_y_values.append(left_gaze[1])
            
        if right_ear >= min_ear_threshold:
            gaze_x_values.append(right_gaze[0])
            gaze_y_values.append(right_gaze[1])
            
        if not gaze_x_values:
            return False
            
        avg_gaze_x = sum(gaze_x_values) / len(gaze_x_values) - self.gaze_ratio_center_x
        avg_gaze_y = sum(gaze_y_values) / len(gaze_y_values) - self.gaze_ratio_center_y
        
        horizontal_looking = abs(avg_gaze_x) < self.gaze_threshold_x
        vertical_looking = abs(avg_gaze_y) < self.gaze_threshold_y
        
        looking_now = horizontal_looking and vertical_looking
        
        self.screen_attention_history.pop(0)
        self.screen_attention_history.append(looking_now)
        
        return sum(self.screen_attention_history) >= len(self.screen_attention_history) // 2

    def start_calibration(self):
        """
        Begin calibration to determine natural center gaze position.
        """
        self.calibration_active = True
        self.calibration_samples = []
        print("Calibration started. Look directly at the center of the screen...")

    def process_calibration(self, left_gaze, right_gaze):
        """
        Process calibration data to set center point.
        
        @param left_gaze: Tuple of (x_ratio, y_ratio) for left eye
        @param right_gaze: Tuple of (x_ratio, y_ratio) for right eye
        """
        if not self.calibration_active:
            return
            
        self.calibration_samples.append((left_gaze, right_gaze))
        
        if len(self.calibration_samples) >= 30:
            left_x_sum = sum(sample[0][0] for sample in self.calibration_samples)
            left_y_sum = sum(sample[0][1] for sample in self.calibration_samples)
            right_x_sum = sum(sample[1][0] for sample in self.calibration_samples)
            right_y_sum = sum(sample[1][1] for sample in self.calibration_samples)
            
            count = len(self.calibration_samples)
            
            avg_left_x = left_x_sum / count
            avg_left_y = left_y_sum / count
            avg_right_x = right_x_sum / count
            avg_right_y = right_y_sum / count
            
            self.gaze_ratio_center_x = (avg_left_x + avg_right_x) / 2
            self.gaze_ratio_center_y = (avg_left_y + avg_right_y) / 2
            
            print(f"Calibration complete!")
            print(f"Center gaze set to: ({self.gaze_ratio_center_x:.3f}, {self.gaze_ratio_center_y:.3f})")
            
            self.calibration_active = False
            self.calibration_complete = True

    def toggle_head_pose_compensation(self):
        """
        Toggle head pose compensation on/off.
        """
        self.use_head_pose_compensation = not self.use_head_pose_compensation
        print(f"Head pose compensation: {'ON' if self.use_head_pose_compensation else 'OFF'}")

    def process_frame(self, frame):
        """
        Process a single frame for eye tracking.
        
        @param frame: Input video frame
        @return: Processed frame with visualizations
        """
        height, width = frame.shape[:2]
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        detection_result = self.landmarker.detect(mp_image)
        
        self.new_frame_time = time.time()
        fps = 1 / (self.new_frame_time - self.prev_frame_time) if (self.new_frame_time - self.prev_frame_time) > 0 else 30
        self.prev_frame_time = self.new_frame_time
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if self.calibration_active:
            cv2.putText(frame, "CALIBRATION ACTIVE - Look at screen center", 
                    (width // 2 - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        
        if detection_result.face_landmarks:
            face_landmarks = detection_result.face_landmarks[0]
            
            landmarks = self.get_landmarks_array(face_landmarks, frame.shape)
            
            landmarks_compensated = landmarks
            head_pose_applied = False
            
            if self.use_head_pose_compensation and detection_result.facial_transformation_matrixes:
                try:
                    transform_matrix = np.array(detection_result.facial_transformation_matrixes[0]).reshape(4, 4)
                    
                    landmarks_np = np.array(landmarks)
                    
                    ones = np.ones((landmarks_np.shape[0], 1))
                    landmarks_homog = np.hstack([landmarks_np, ones])
                    
                    transformed = (transform_matrix @ landmarks_homog.T).T
                    
                    w = transformed[:, 3].reshape(-1, 1)
                    w[w == 0] = 1
                    transformed = transformed[:, :3] / w
                    
                    landmarks_compensated = transformed.tolist()
                    head_pose_applied = True
                except Exception as e:
                    print(f"Error applying head pose compensation: {e}")
                    landmarks_compensated = landmarks
            
            if self.show_mesh:
                connections = mp.solutions.face_mesh.FACEMESH_TESSELATION
                connections_list = list(connections)
                for i in range(0, len(connections_list), 8):
                    if i < len(connections_list):
                        connection = connections_list[i]
                        start_idx, end_idx = connection
                        if not self.show_eyes_only or (start_idx not in self.LEFT_EYE_OUTLINE + self.RIGHT_EYE_OUTLINE and 
                                                        end_idx not in self.LEFT_EYE_OUTLINE + self.RIGHT_EYE_OUTLINE):
                            cv2.line(frame, 
                                    (int(landmarks[start_idx][0]), int(landmarks[start_idx][1])),
                                    (int(landmarks[end_idx][0]), int(landmarks[end_idx][1])),
                                    (70, 70, 70), 1)
            
            for idx in self.LEFT_EYE_OUTLINE:
                cv2.circle(frame, (int(landmarks[idx][0]), int(landmarks[idx][1])), 1, (0, 255, 255), -1)
            for idx in self.RIGHT_EYE_OUTLINE:
                cv2.circle(frame, (int(landmarks[idx][0]), int(landmarks[idx][1])), 1, (0, 255, 255), -1)
            
            for idx in self.LEFT_IRIS:
                cv2.circle(frame, (int(landmarks[idx][0]), int(landmarks[idx][1])), 1, (255, 0, 0), -1)
            for idx in self.RIGHT_IRIS:
                cv2.circle(frame, (int(landmarks[idx][0]), int(landmarks[idx][1])), 1, (255, 0, 0), -1)
            
            left_ear = self.calculate_ear(landmarks_compensated, self.LEFT_EYE_VERTICAL, self.LEFT_EYE_HORIZONTAL)
            right_ear = self.calculate_ear(landmarks_compensated, self.RIGHT_EYE_VERTICAL, self.RIGHT_EYE_HORIZONTAL)
            
            left_gaze_data = self.calculate_gaze_ratio(
                landmarks_compensated, self.LEFT_EYE_OUTLINE, self.LEFT_IRIS)
            right_gaze_data = self.calculate_gaze_ratio(
                landmarks_compensated, self.RIGHT_EYE_OUTLINE, self.RIGHT_IRIS)
            
            left_gaze = (left_gaze_data[0], left_gaze_data[1])
            right_gaze = (right_gaze_data[0], right_gaze_data[1])
            left_eye_center = left_gaze_data[2]
            right_eye_center = right_gaze_data[2]
            left_iris_center = left_gaze_data[3]
            right_iris_center = right_gaze_data[3]
            
            if self.calibration_active:
                self.process_calibration(left_gaze, right_gaze)
            
            cv2.circle(frame, (int(left_eye_center[0]), int(left_eye_center[1])), 3, (0, 165, 255), -1)
            cv2.circle(frame, (int(right_eye_center[0]), int(right_eye_center[1])), 3, (0, 165, 255), -1)
            cv2.circle(frame, (int(left_iris_center[0]), int(left_iris_center[1])), 3, (0, 255, 0), -1)
            cv2.circle(frame, (int(right_iris_center[0]), int(right_iris_center[1])), 3, (0, 255, 0), -1)
            
            scale = 60
            left_gaze_endpoint = (
                int(left_eye_center[0] + left_gaze[0] * scale),
                int(left_eye_center[1] + left_gaze[1] * scale)
            )
            right_gaze_endpoint = (
                int(right_eye_center[0] + right_gaze[0] * scale),
                int(right_eye_center[1] + right_gaze[1] * scale)
            )
            
            cv2.line(frame, 
                    (int(left_eye_center[0]), int(left_eye_center[1])), 
                    left_gaze_endpoint, 
                    (0, 0, 255), 2)
            cv2.line(frame, 
                    (int(right_eye_center[0]), int(right_eye_center[1])), 
                    right_gaze_endpoint, 
                    (0, 0, 255), 2)
            
            self.looking_at_screen = self.is_looking_at_screen(left_gaze, right_gaze, left_ear, right_ear)
            self.brain_rot.not_focused(focused=self.looking_at_screen)

            eyes_open_text = f"Eyes Open: L: {left_ear:.2f}, R: {right_ear:.2f}"
            cv2.putText(frame, eyes_open_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            raw_gaze_text = f"Raw gaze: L: ({left_gaze[0]:.2f}, {left_gaze[1]:.2f}), R: ({right_gaze[0]:.2f}, {right_gaze[1]:.2f})"
            
            if self.calibration_complete:
                rel_left_x = left_gaze[0] - self.gaze_ratio_center_x
                rel_left_y = left_gaze[1] - self.gaze_ratio_center_y
                rel_right_x = right_gaze[0] - self.gaze_ratio_center_x
                rel_right_y = right_gaze[1] - self.gaze_ratio_center_y
                
                rel_gaze_text = f"Relative to center: L: ({rel_left_x:.2f}, {rel_left_y:.2f}), R: ({rel_right_x:.2f}, {rel_right_y:.2f})"
                cv2.putText(frame, rel_gaze_text, (10, 90), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            thresh_text = f"Thresh: X: ±{self.gaze_threshold_x:.2f}, Y: ±{self.gaze_threshold_y:.2f}"
            head_pose_text = f"Head Comp: {'ON' if self.use_head_pose_compensation else 'OFF'}"
            hp_status = f"{' (applied)' if head_pose_applied else ' (not applied)'}" if self.use_head_pose_compensation else ""
            
            cv2.putText(frame, thresh_text + " | " + head_pose_text + hp_status, (10, 120), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if self.debug_level >= 1:
                cv2.putText(frame, raw_gaze_text, (10, 150), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                          
                calib_text = f"Center: ({self.gaze_ratio_center_x:.2f}, {self.gaze_ratio_center_y:.2f})"
                cv2.putText(frame, calib_text, (10, 180), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            status_text = "Looking at Screen: YES" if self.looking_at_screen else "Looking at Screen: NO"
            status_color = (0, 255, 0) if self.looking_at_screen else (0, 0, 255)
            cv2.putText(frame, status_text, (10, height - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        else:
            cv2.putText(frame, "No face detected", (10, height - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.putText(frame, "c: calibrate, h: head comp, m: mesh, d: debug, arrow/WASD: thresholds, q: quit", 
                   (10, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def adjust_thresholds(self, x_delta=0, y_delta=0):
        """
        Adjust the gaze thresholds.
        
        @param x_delta: Change to apply to horizontal threshold
        @param y_delta: Change to apply to vertical threshold
        """
        self.gaze_threshold_x = max(0.05, min(0.5, self.gaze_threshold_x + x_delta))
        self.gaze_threshold_y = max(0.05, min(0.5, self.gaze_threshold_y + y_delta))
        print(f"Thresholds adjusted to X: ±{self.gaze_threshold_x:.2f}, Y: ±{self.gaze_threshold_y:.2f}")
    
    def toggle_mesh(self):
        """
        Toggle face mesh visibility.
        """
        self.show_mesh = not self.show_mesh
        print(f"Face mesh display: {'ON' if self.show_mesh else 'OFF'}")
    
    def toggle_debug_level(self):
        """
        Cycle through debug visualization levels.
        """
        self.debug_level = (self.debug_level + 1) % 3
        print(f"Debug level: {self.debug_level}")

def main():
    """
    Main function to run the eye gaze tracker.
    
    Command line usage:
    python brainrot_eyedetection.py --backend_url http://localhost:5001 --user_id user123
    """
    import os
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Eye Gaze Tracker with Brain Rot Detection')
    parser.add_argument('--backend_url', type=str, default='http://localhost:5001',
                        help='URL of the Flask backend')
    parser.add_argument('--user_id', type=str, default='test_user',
                        help='User ID for the current session')
    args = parser.parse_args()
    
    print(f"Backend URL: {args.backend_url}")
    print(f"User ID: {args.user_id}")
    
    if not os.path.exists('face_landmarker.task'):
        print("Downloading face landmarker model...")
        import urllib.request
        urllib.request.urlretrieve(
            'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
            'face_landmarker.task')
        print("Model downloaded successfully!")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    tracker = EyeGazeTracker(backend_url=args.backend_url, user_id=args.user_id)
    
    print("Eye Gaze Tracker Started")
    print("Press 'c' to calibrate (look at screen center)")
    print("Press 'h' to toggle head pose compensation")
    print("Press 'm' to toggle face mesh")
    print("Press 'd' to cycle debug info")
    print("Use arrow keys or WASD to adjust thresholds")
    print("Press 'r' to reset brain rot trigger")
    print("Press 'q' to quit")
    
    # Display brain rot detection info
    print(f"\nBrain Rot Detection:")
    print(f"  Trigger threshold: {tracker.brain_rot.trigger_threshold} look-away events")
    print(f"  Look-away duration: {tracker.brain_rot.look_away_duration} seconds per event")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        processed_frame = tracker.process_frame(frame)
        
        cv2.imshow('Eye Gaze Tracker', processed_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            tracker.start_calibration()
        elif key == ord('h'):
            tracker.toggle_head_pose_compensation()
        elif key == ord('m'):
            tracker.toggle_mesh()
        elif key == ord('d'):
            tracker.toggle_debug_level()
        elif key == 82 or key == ord('w'):
            tracker.adjust_thresholds(y_delta=-0.01)
        elif key == 84 or key == ord('s'):
            tracker.adjust_thresholds(y_delta=0.01)
        elif key == 81 or key == ord('a'):
            tracker.adjust_thresholds(x_delta=-0.01)
        elif key == 83 or key == ord('d'):
            tracker.adjust_thresholds(x_delta=0.01)
        elif key == ord('r'):
            tracker.brain_rot.reset_trigger()
            print("Brain rot trigger reset")
    
    if not tracker.brain_rot.is_focused and tracker.brain_rot.last_unfocus_time is not None:
        final_unfocused_duration = time.perf_counter() - tracker.brain_rot.last_unfocus_time
        tracker.brain_rot.not_focused_times += final_unfocused_duration
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Calculate and format time metrics
    total_seconds = tracker.brain_rot.not_focused_times
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    
    print("\nBrain Rot Warning Statistics:")
    print(f"Times looked away from screen: {tracker.brain_rot.times_not_looking_at_screen}")
    print(f"Total time not looking at screen: {minutes} min {seconds:.2f} sec")
    print("Tracker ended")

if __name__ == "__main__":
    main()