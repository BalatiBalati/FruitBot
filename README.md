# FruitBot

This project uses a robotic arm and a camera to detect and sort fruits based on their ripeness. It leverages a Roboflow inference API to classify fruits as ripe or unripe/rotten and then moves them to the corresponding bin.

## Overview

1. **Camera Capture**: The system continuously captures frames from the webcam.
2. **Fruit Detection & Classification**: Each captured frame is sent to a Roboflow model for inference. The model returns fruit predictions along with their confidence scores.
3. **Robotic Arm Control**: 
   - The arm moves to predefined positions to pick up the detected fruit.
   - Depending on the classification (ripe or unripe/rotten), the arm places the fruit into the correct bin.

## Key Components

- **Robotic Arm**: Controlled by the `Arm_Lib` module, which provides methods for moving the arm to specific angles and for operating the gripper.
- **InferenceHTTPClient**: Interacts with the Roboflow API to get object detection predictions.
- **Positions**:
  - `p_mould`: The neutral "home" position of the arm.
  - `p_top`: Intermediate lifting position.
  - `p_pickup`: Position for picking up the fruit.
  - `p_ripe`: Position of the bin for ripe fruit (yellow bin).
  - `p_unripe`: Position of the bin for unripe/rotten fruit (red bin).

## Installation & Setup

1. **Hardware Setup**:
   - Connect the Dofbot robotic arm properly to the Raspberry Pi and the power source.
   - Connect the Camera USB to the Raspberry Pi.
   - Ensure the Raspberry Pi is connected to the internet for Roboflow API access.
   - Ensure all components are connected as indicated in the Dofbot manual

2. **Dependencies**:
   - `Python 3`
   - `opencv-python` for camera input and image processing.
   - `numpy`
   - `base64`
   - `time`
   - `inference_sdk` (custom or provided by Roboflow)
   - `Arm_Lib` (custom library for the robotic arm)
   - `ipywidgets` and `IPython.display` for the interactive UI.

    #### Install dependencies with pip:
    >bash
    ```
    pip install opencv-python numpy base64 time inference_sdk Arm_Lib ipywidgets IPython
    ```

3. **Roboflow API**:
   - Use a roboflow API and passing into the `InferenceHTTPClient` initialization.
    >Python
    ```
    api_url="https://detect.roboflow.com",
    api_key="xOq95WwD7YPT7VB1F9KD"
    ```

4. **Run the Code**:
   - This code is to be run in a *Jupyter notebook* environment to access `ipywidgets` and `display`.
   - After starting a Jupyter notebook session, run the provided code cell. The UI should appear with `Start Sorting` and `Stop Sorting` buttons.
   - Click `Start Sorting` to begin the process.

## How It Works

1. **Starting the Process**:
   - Press the `Start Sorting` button. The webcam starts capturing frames.
   - Each frame is sent to Roboflow to detect fruits and their ripeness.

2. **Fruit Detection**:
   - If a fruit is detected and the confidence is above `0.5`, the robotic arm sequence starts.
   - The arm moves to the pickup position, closes its gripper to pick up the fruit, and then moves to the respective bin based on the classification.

3. **Classification Logic**:
   - If the detected fruit class contains the word "*ripe*", it is considered ripe and placed in the yellow bin.
   - If the detected fruit class contains "*rotten*" or is otherwise unripe, it goes to the red bin.

4. **Displaying Results**:
   - As fruits are sorted, the text area updates with the sorted fruit information (*fruit type*, *confidence*, and *bin location*).

5. **Stopping the Process**:
   - Press `Stop Sorting` to terminate the operation. The arm returns home, and the camera is released.

## Troubleshooting

- **No Camera Found**: Ensure the webcam is properly connected and recognized by the system.
- **No Fruits Detected**: Ensure that the camera has a clear view of the fruits. Check the lighting conditions or move the fruit closer.
- **Robotic Arm Not Moving**: Verify the `Arm_Lib` setup and that the robotic arm is powered and correctly connected.

## Team

- **Balati Albert** (Development & Arm Integration):
    - Functions for arm movement and gripper control (`arm_clamp_block, arm_move`).
    - Core logic to pick up and sort fruit (`pick_up_and_sort_fruit`).
- **Shima Sarah** (Debugging & Performance):
    - Communicating with Roboflow (`get_prediction_from_roboflow`).
    - Main control loop and threading in `FruitSortingController._run_sorting`.
    - Error handling, performance refinements.
- **Shabaz** (Feedback, Testing & UI):: 
    - User interface elements (`ipywidgets`, `display` logic).
    - The `run_fruit_sorting()` function and testing suggestions.
- **Vighnesh** (Initial Setup & Feasibility):
    - Imports, initial setup, arm position arrays, arm initialization.
    - Setting up the `InferenceHTTPClient` for Roboflow.
