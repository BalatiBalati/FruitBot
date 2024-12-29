import cv2
import base64
import numpy as np
import time
from inference_sdk import InferenceHTTPClient
from Arm_Lib import Arm_Device
import threading
import ipywidgets as widgets
from IPython.display import display, clear_output, Image

# Predefined arm positions
p_mould = [90, 130, 0, 0, 90]    # Home/neutral position
p_top = [90, 80, 50, 50, 270]    # Intermediate lifting position
p_pickup = [90, 53, 60, 20, 270] # Pickup position
p_ripe = [25, 135, 0, 0, 90]     # Yellow bin (for ripe fruits)
p_unripe = [175, 135, 0, 0, 90]  # Red bin (for unripe/rotten fruits)

# Initialize Arm
Arm = Arm_Device()
time.sleep(0.1)

# Create an inference client to interact with the Roboflow API
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="xOq95WwD7YPT7VB1F9KD"
)

# Function to convert image to base64 format
def image_to_base64(image):
    _, img_encoded = cv2.imencode('.jpg', image)
    return base64.b64encode(img_encoded).decode('utf-8')

# Function to send the base64 image to Roboflow API and get predictions
def get_prediction_from_roboflow(image):
    img_base64 = image_to_base64(image)
    response = CLIENT.infer(img_base64, model_id="fruits-opg9g/1")
    return response

# Arm movement functions
def arm_clamp_block(enable, max_attempts=50, step=5, delay=0.1):

    """
    Control gripper to adjust based on fruit size.  
    :param enable: 0 to open the gripper, 1 to close the gripper.
    :param max_attempts: Maximum number of attempts to tighten the grip.
    :param step: Step size for tightening angle.
    :param delay: Delay between adjustments for stability.

    """
    if enable == 0:
        # Open the gripper to a wide angle
        Arm.Arm_serial_servo_write(6, 60, 400)
    else:
        # Gradually tighten the gripper
        for attempt in range(max_attempts):
            current_angle = Arm.Arm_serial_servo_read(6)  # Read the current angle
            next_angle = current_angle + step  # Increment angle for tightening
            # Send command to tighten
            Arm.Arm_serial_servo_write(6, next_angle, 200)
            time.sleep(delay)  # Allow time for servo to move
            # Check the new angle after the command
            new_angle = Arm.Arm_serial_servo_read(6)
            # If the servo angle does not change, assume grip is tight
            if abs(new_angle - next_angle) < 1:  # Threshold for detecting no movement
                print(f"Grip detected at angle: {new_angle}")
                break
        else:
            print("Max attempts reached, grip might not be perfect.")
    # Small delay for stability

    time.sleep(0.5)
def arm_move(p, s_time=500):
    """Move arm to specific position"""
    for i in range(5):
        id = i + 1
        if id == 5:
            time.sleep(0.1)
            Arm.Arm_serial_servo_write(id, p[i], int(s_time * 1.2))
        else:
            Arm.Arm_serial_servo_write(id, p[i], s_time)
        time.sleep(0.01)
    time.sleep(s_time / 1000)

def pick_up_and_sort_fruit(is_ripe, ready_flag):
    """Pick up and sort fruit based on ripeness"""
    try:
        # Initial setup
        arm_clamp_block(0)
        arm_move(p_mould, 1000)
        time.sleep(0.5)

        # Move to top position
        arm_move(p_top, 1000)

        # Move to pickup position
        arm_move(p_pickup, 1000)

        # Grab the fruit
        arm_clamp_block(1)

        # Lift to top position
        arm_move(p_top, 1000)

        # Move to appropriate bin based on ripeness
        if is_ripe:
            arm_move(p_ripe, 1000)
        else:
            arm_move(p_unripe, 1000)

        # Release fruit
        arm_clamp_block(0)

        # Return to home position
        arm_move(p_mould, 1000)
        time.sleep(0.5)

    except Exception as e:
        print(f"Error in picking and sorting fruit: {e}")

    # Signal that the arm is ready for the next capture
    ready_flag.set()

class FruitSortingController:
    def __init__(self):
        # Create widgets for display and control
        self.output = widgets.Output()
        self.status_label = widgets.Label(value="Sorting System Ready")
        self.start_button = widgets.Button(description="Start Sorting")
        self.stop_button = widgets.Button(description="Stop Sorting")
        self.sorted_fruits_output = widgets.Textarea(
            value="Sorted Fruits will appear here",
            layout=widgets.Layout(width='100%', height='200px')
        )

        # Threading control variables
        self.sorting_active = threading.Event()
        self.sorted_fruits = []

        # Setup button interactions
        self.start_button.on_click(self.start_sorting)
        self.stop_button.on_click(self.stop_sorting)
       
        # Disable stop button initially
        self.stop_button.disabled = True

    def display_controls(self):
        """Display the control widgets"""
        display(
            self.status_label,
            self.start_button,
            self.stop_button,
            self.sorted_fruits_output,
            self.output
        )

    def start_sorting(self, b=None):
        # Set active flag
        self.sorting_active.set()
       
        # Update UI state
        self.status_label.value = "Sorting in Progress..."
        self.start_button.disabled = True
        self.stop_button.disabled = False

        # Start sorting in a separate thread
        threading.Thread(target=self._run_sorting, daemon=True).start()

    def stop_sorting(self, b=None):
        # Clear active flag
        self.sorting_active.clear()
       
        # Update UI state
        self.status_label.value = "Sorting Stopped"
        self.start_button.disabled = False
        self.stop_button.disabled = True

    def _run_sorting(self):
        # Open the front camera (webcam)
        cap = cv2.VideoCapture(0)

        # Check if the webcam is opened properly
        if not cap.isOpened():
            self.status_label.value = "Error: Could not access the camera."
            self.stop_sorting()
            return

        ready_flag = threading.Event()
        ready_flag.set()  # Initial state is ready

        try:
            while self.sorting_active.is_set():
                # Wait until the robot is ready for the next capture
                ready_flag.wait()

                # Clear the frame buffer to avoid stale frames
                for _ in range(5):
                    cap.read()

                ret, frame = cap.read()
                if not ret:
                    self.status_label.value = "Error: Failed to capture frame."
                    break

                # Get predictions from Roboflow API for the current frame
                predictions = get_prediction_from_roboflow(frame)

                # Process predictions
                if 'predictions' in predictions:
                    predicted_classes = predictions['predicted_classes']
                    for fruit in predicted_classes:
                        confidence = predictions['predictions'][fruit]['confidence']

                        if "ripe" in fruit.lower():
                            is_ripe = True
                            bin_location = "YELLOW (Ripe)"
                        elif "rotten" in fruit.lower():
                            is_ripe = False
                            bin_location = "RED (Unripe/Rotten)"
                        else:
                            is_ripe = False
                            bin_location = "RED (Unripe)"

                        if confidence > 0.5:
                            ready_flag.clear()
                            threading.Thread(target=pick_up_and_sort_fruit, args=(is_ripe, ready_flag)).start()
                            self.sorted_fruits.append({
                                'fruit': fruit,
                                'confidence': confidence,
                                'bin': bin_location
                            })
                           
                            # Update sorted fruits display
                            self.sorted_fruits_output.value = "\n".join([
                                f"Fruit: {fruit['fruit']}, Confidence: {fruit['confidence']:.2f}, Bin: {fruit['bin']}"
                                for fruit in self.sorted_fruits
                            ])
                else:
                    self.status_label.value = "No fruits detected. Try again!"

                # Small delay to allow frame refresh
                time.sleep(0.5)

        finally:
            # Release the camera and cleanup resources
            cap.release()
            self.status_label.value = "Camera released."
            self.stop_sorting()

# Run the fruit sorting application
def run_fruit_sorting():
    controller = FruitSortingController()
    controller.display_controls()

# Run the fruit sorting application
run_fruit_sorting()