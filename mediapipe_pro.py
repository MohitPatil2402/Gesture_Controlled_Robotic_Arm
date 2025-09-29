import cv2
import mediapipe as mp
import socket
import time
import math

# ==============================
# ESP8266 UDP settings
# ==============================
UDP_IP = "127.0.0.1"  # Replace with your ESP8266 IP
UDP_PORT = 1234
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ==============================
# MediaPipe Hands
# ==============================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# ==============================
# Settings
# ==============================
FINGER_TIPS = [8, 12, 16, 20]  # index, middle, ring, pinky
MOVEMENT_THRESHOLD = 0.015  # Lowered for more sensitive movement detection
HAND_SIZE_THRESHOLD = 0.02  # Threshold for hand size change to detect forward/backward
MOVEMENT_GRACE_PERIOD = 1.0  # Grace period after movement stops before checking fingers

def count_extended_fingers(landmarks):
    extended = 0
    for tip in FINGER_TIPS:
        if landmarks[tip].y < landmarks[tip - 2].y:  # Tip above PIP joint
            extended += 1
    return extended

def get_hand_size(landmarks):
    """Calculate hand size based on distance between key points"""
    wrist = landmarks[0]
    middle_tip = landmarks[12]
    distance = math.sqrt((wrist.x - middle_tip.x)**2 + (wrist.y - middle_tip.y)**2)
    return distance

def get_gesture(landmarks, prev_wrist, prev_hand_size, last_movement_time):
    wrist = landmarks[0]
    gesture = None
    current_time = time.time()

    fingers = count_extended_fingers(landmarks)
    current_hand_size = get_hand_size(landmarks)

    # ===== PRIORITY: GRAB / RELEASE =====
    if fingers == 0:
        return "GRAB", False, current_hand_size
    elif fingers == 1:
        return "RELEASE", False, current_hand_size

    # ===== MOVEMENT PRIORITY =====
    movement_detected = False
    if prev_wrist and prev_hand_size:
        dx = wrist.x - prev_wrist.x
        dy = wrist.y - prev_wrist.y
        dsize = current_hand_size - prev_hand_size

        if (abs(dx) > MOVEMENT_THRESHOLD or 
            abs(dy) > MOVEMENT_THRESHOLD or 
            abs(dsize) > HAND_SIZE_THRESHOLD):
            movement_detected = True
            
            # Prioritize forward/backward based on hand size change
            if abs(dsize) > HAND_SIZE_THRESHOLD:
                if dsize > HAND_SIZE_THRESHOLD:
                    gesture = "FORWARD"  # Hand getting larger (moving closer)
                elif dsize < -HAND_SIZE_THRESHOLD:
                    gesture = "BACKWARD"  # Hand getting smaller (moving away)
            # Then check X/Y movement
            elif abs(dx) > abs(dy):
                if dx < -MOVEMENT_THRESHOLD: 
                    gesture = "LEFT"
                elif dx > MOVEMENT_THRESHOLD: 
                    gesture = "RIGHT"
            else:
                if dy < -MOVEMENT_THRESHOLD: 
                    gesture = "UP"
                elif dy > MOVEMENT_THRESHOLD: 
                    gesture = "DOWN"
    
    # If no movement detected, check if we're still in grace period
    if not movement_detected:
        # If we recently had movement, don't send any command during grace period
        if last_movement_time and (current_time - last_movement_time) < MOVEMENT_GRACE_PERIOD:
            gesture = None  # No command during grace period
        else:
            # Grace period over, check finger-based commands
            if fingers == 0:
                gesture = "GRAB"
            elif fingers == 1:
                gesture = "RELEASE"
            elif fingers == 2:
                gesture = "BACKWARD"  # Finger-based backward command
            elif fingers >= 4:
                gesture = "STOP"
            # Don't send anything for 3 fingers or other cases
    
    return gesture, movement_detected, current_hand_size

# ==============================
# Colors for overlay text
# ==============================
COMMAND_COLORS = {
    "LEFT": (255, 0, 0),        # Blue
    "RIGHT": (0, 0, 255),       # Red
    "UP": (0, 255, 0),          # Green
    "DOWN": (0, 255, 255),      # Yellow
    "FORWARD": (255, 165, 0),   # Orange
    "BACKWARD": (255, 0, 255),  # Magenta
    "GRAB": (128, 0, 128),      # Purple
    "RELEASE": (255, 192, 203), # Pink
    "STOP": (0, 0, 0),          # Black
}

# ==============================
# Main loop
# ==============================
cap = cv2.VideoCapture(0)
prev_wrist = None
prev_hand_size = None
last_command = ""
cooldown = 0.75
last_time = 0
current_cmd = "NONE"  # No default command
last_movement_time = None  # Track when movement last occurred

print("🚀 Gesture control started")
print("Mode: MOVEMENT PRIORITY with FORWARD/BACKWARD detection")
print("Move hand closer/farther for FORWARD/BACKWARD")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmarks = hand_landmarks.landmark

            gesture, movement_detected, current_hand_size = get_gesture(
                landmarks, prev_wrist, prev_hand_size, last_movement_time)
            
            prev_wrist = landmarks[0]
            prev_hand_size = current_hand_size
            
            # Update movement time if movement was detected
            if movement_detected:
                last_movement_time = time.time()

            # Only send command if gesture is not None
            if gesture is not None:
                # Send command with reduced cooldown for movement commands
                movement_commands = ["LEFT", "RIGHT", "UP", "DOWN", "FORWARD", "BACKWARD"]
                current_cooldown = 0.3 if gesture in movement_commands else cooldown
                
                if (gesture != last_command or 
                   (time.time() - last_time) > current_cooldown):
                    print(f"Sending: {gesture}")
                    sock.sendto(gesture.encode(), (UDP_IP, UDP_PORT))
                    last_command = gesture
                    last_time = time.time()
                    current_cmd = gesture  # update overlay
            else:
                current_cmd = "NONE"  # Show no command when gesture is None

    # ==============================
    # Show command on screen with movement priority indicator
    # ==============================
    color = COMMAND_COLORS.get(current_cmd, (128, 128, 128))  # Gray for NONE
    cv2.putText(frame, f"CMD: {current_cmd}", (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 4)
    
    # Show finger count and hand size for debugging
    if result.multi_hand_landmarks:
        finger_count = count_extended_fingers(result.multi_hand_landmarks[0].landmark)
        hand_size = get_hand_size(result.multi_hand_landmarks[0].landmark)
        cv2.putText(frame, f"Fingers: {finger_count}", (30, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Hand Size: {hand_size:.3f}", (30, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
        break

cap.release()
cv2.destroyAllWindows()