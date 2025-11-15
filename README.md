# Paul The Robot Baby

This project is a human-robot interaction study that involves a physical robot controlled by an Arduino and a Python-based GUI for user interaction. The robot, named "Paul," is designed to assist in a quality control task of inspecting Printed Circuit Boards (PCBs).

## Quick Start Guide

1.  **Setup the hardware and software** by following the [Setup](#setup) instructions below.
2.  **Install Python packages**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the GUI**:
    ```bash
    python AnthroGUI.py
    ```

## Project Overview

The project consists of three main components:

1.  **Arduino-controlled Robot**: A physical robot built with a MeMegaPi board that controls motors and sensors. It receives commands via Bluetooth to perform actions like scanning PCBs, moving, and operating an arm.
2.  **Python GUI**: A desktop application built with `tkinter` that serves as the user interface for the study. It presents a series of trials to the user, sends commands to the robot, and collects user responses and survey data.
3.  **Supporting Files**: A collection of text files that provide content for the GUI, such as consent forms, instructions, and narrative elements for the study.

## File Descriptions

### Code

*   `AnthroFraming_09-04-24.ino`: An Arduino sketch that runs on the MeMegaPi board. It controls the robot's motors for movement and the arm, and reads data from line-following sensors. It communicates with the Python GUI via a serial connection (Bluetooth).
*   `AnthroGUI.py`: The main Python application for the user study. It uses `tkinter` to create a graphical user interface that guides the user through a consent form, questionnaires, and the main experimental task. It communicates with the Arduino to control the robot.
*   `Bluetooth-Example.py`: A simplified Python script for testing Bluetooth communication with the robot.
*   `requirements.txt`: A list of Python packages required to run the GUI.

### Text and Data Files

*   `CONSENT.txt`: A text file containing the consent form for the research study. This is displayed to the user at the beginning of the experiment.
*   `FRAMING_anthro.txt`: A text file containing an anthropomorphic description of the robot "Paul." This is used in one of the experimental conditions.
*   `FRAMING_tech.txt`: A text file containing a technical description of the robot. This is used in the other experimental condition.
*   `IDAQ instructions`: Instructions for the Individual Differences in Anthropomorphism Questionnaire (IDAQ).
*   `INSTRUCTIONS.txt`: Instructions for the user on how to perform the PCB inspection task.
*   `PROMPT.txt`: A text file containing the main prompt for the user, explaining the task.
*   `STORY.txt`: A narrative background story for the user to read before starting the task.

## Hardware (from `AnthroFraming_09-04-24.ino`)

*   **Microcontroller**: MeMegaPi (based on Arduino Mega)
*   **Motors**:
    *   `motor1`: Left motor (PORT1B)
    *   `motor2`: Arm motor (PORT2B)
    *   `motor3`: Right motor (PORT3B)
    *   `motor4`: Unused (PORT4B)
*   **Sensors**:
    *   `LEFT_SENSOR_PIN`: 69
    *   `RIGHT_SENSOR_PIN`: 68
*   **Communication**: Bluetooth via Serial3 (TX: 14, RX: 15)
*   **Other**: LED on pin 13

## Software

### Arduino Sketch (`AnthroFraming_09-04-24.ino`)

The Arduino sketch is responsible for the low-level control of the robot. It listens for single-character commands over the serial port and executes the corresponding functions.

#### Functions

*   `setup()`: Initializes the pins, serial communication, and motors.
*   `stopMotors()`: Stops the left and right motors.
*   `quickCenter()`: A centering function that makes small adjustments based on sensor readings.
*   `delayWithChecks(int ms)`: A delay function that also performs `quickCenter()` checks.
*   `startMotorsWithBoost(int16_t leftSpeed, int16_t rightSpeed)`: Starts the motors with a short boost of speed to overcome inertia.
*   `lowerArm()`: Lowers the robot's arm.
*   `raiseArm()`: Raises the robot's arm.
*   `scanChip()`: A sequence of movements to simulate scanning a PCB chip.
*   `curveTurn()`: A function to make the robot turn along a curved path.
*   `nextChip()`: Moves the robot to the next chip in the sequence.
*   `loop()`: The main loop that waits for serial commands and executes the corresponding actions.

#### Serial Commands

*   `'1'`: `scanChip()` - Performs a normal scan.
*   `'2'`: `lowerArm()`, `scanChip()`, `raiseArm()` - Performs a "zoomed" scan.
*   `'3'`: `nextChip()` - Moves to the next chip.

### Python GUI (`AnthroGUI.py`)

The Python GUI is a `tkinter` application that manages the user study.

#### Classes

*   `SurveyApp(tk.Tk)`: The main application class.

#### Methods

*   `__init__()`: Initializes the application, sets up trial parameters, loads text files, and starts the consent screen.
*   `connect_bluetooth()`: Establishes a serial connection with the robot over Bluetooth.
*   `normal_scan()`: Sends the `'1'` command to the robot.
*   `zoom_scan()`: Sends the `'2'` command to the robot.
*   `next_chip()`: Sends the `'3'` command to the robot.
*   `generate_experimental_trials()`: Creates a list of trials for the main experiment.
*   `is_salient()`: Determines the robot's recommendation based on the trial parameters.
*   `save_results()`: Saves the collected data to a CSV file.
*   `generate_damage_pattern()`: Creates a visual representation of a damaged PCB.
*   `add_border()`: Adds a border to the generated image.
*   `show_consent()`: Displays the consent form.
*   `show_LAB_questions()`, `show_PROPENSITY_questions()`, `show_IDAQ_questions()`: Display various questionnaires.
*   `show_story()`, `show_framing()`, `show_instructions()`: Display the narrative and instructional screens.
*   `show_waiting_screen()`: Displays a loading screen while the robot is moving.
*   `show_trial()`: Displays the main trial screen with the PCB image and buttons.
*   `initiate_zoom_scan()`: Initiates the zoom scan sequence.
*   `show_zoom_image()`: Displays the zoomed-in image.
*   `accept_with_next()`, `reject_with_next()`: Handlers for the user's response.
*   `record_response()`: Records the user's response and other trial data.
*   `show_transition()`: A screen shown between the practice and main trials.
*   `start_main_trials()`: Starts the main experimental trials.
*   `show_end()`: The final screen of the experiment.
*   `on_closing()`: A handler for when the application window is closed.
*   `clear_screen()`: Clears all widgets from the application window.

## Setup

### Arduino Setup

1.  **Install Arduino IDE**: Download and install the [Arduino IDE](https://www.arduino.cc/en/software) for your operating system.
2.  **Install MeMegaPi Library**:
    *   In the Arduino IDE, go to `Sketch > Include Library > Manage Libraries...`.
    *   Search for "MeMegaPi" and install the library by Makeblock.
3.  **Connect the MeMegaPi Board**:
    *   Plug the MeMegaPi board into your computer using a USB cable.
    *   Power on the board.
4.  **Select Board and Port**:
    *   In the Arduino IDE, go to `Tools > Board` and select "Arduino Mega or Mega 2560".
    *   Go to `Tools > Port` and select the serial port corresponding to your MeMegaPi board.
5.  **Verify and Flash the Code**:
    *   Open the `AnthroFraming_09-04-24.ino` file in the Arduino IDE.
    *   Click the "Verify" button (checkmark icon) to compile the code and check for errors.
    *   Click the "Upload" button (arrow icon) to flash the code to the MeMegaPi board.
6.  **MeMegaPi Datasheet**: For more information on the MeMegaPi board and pin information, refer to the [Makeblock Me MegaPi documentation](https://www.makeblock.com/project/me-megapi).

### Python Setup

1.  **Install Python**: Download and install [Python](https://www.python.org/downloads/) (version 3.6 or higher) for your operating system.
2.  **Install Visual Studio Code**: Download and install [Visual Studio Code](https://code.visualstudio.com/), a popular code editor.
3.  **Find the Bluetooth Serial Port**:
    *   **Windows**: Open the Device Manager, expand the "Ports (COM & LPT)" section, and look for the serial port associated with your Bluetooth module (e.g., `COM3`).
    *   **macOS**: Open the Terminal and run `ls /dev/tty.*`. Look for a device that corresponds to your Bluetooth module (e.g., `/dev/tty.Bluetooth-Incoming-Port`).
    *   **Linux**: Open the Terminal and run `ls /dev/tty*`. Look for a device like `/dev/ttyUSB0` or `/dev/ttyACM0`.
4.  **Update the Port in `AnthroGUI.py`**:
    *   Open `AnthroGUI.py` in VS Code or your preferred editor.
    *   Find the line `self.bluetooth_port = 'COM3'` and replace `'COM3'` with the serial port you found in the previous step.
5.  **Install Python Packages**:
    *   Open a terminal or command prompt in the project directory.
    *   Run the following command to install the required packages:
        ```bash
        pip install -r requirements.txt
        ```

## How to Run

1.  **Hardware Setup**:
    *   Ensure the `AnthroFraming_09-04-24.ino` sketch is uploaded to the MeMegaPi board.
    *   Power on the robot.
    *   Ensure the Bluetooth module is connected and paired with the computer running the Python GUI.

2.  **Software Setup**:
    *   Ensure you have completed the [Python Setup](#python-setup) steps.
    *   Run the `AnthroGUI.py` script:
        ```bash
        python AnthroGUI.py
        ```

## Data Collection

The `AnthroGUI.py` application collects the following data:

*   **Session ID**: A unique ID for each experimental session, based on the start time.
*   **User Responses**: For each trial, the application records:
    *   Trial number
    *   Trial type (practice or experimental)
    *   Damage percentage
    *   Whether the trial was "salient" (i.e., if the robot's recommendation was intentionally misleading)
    *   The user's response ("Accept" or "Reject")
    *   Whether the user's response was correct
    *   Whether the user used the zoom function
*   **Questionnaire Data**: The application collects responses from several questionnaires (LAB, PROPENSITY, IDAQ, TOROS, MULTID).
*   **Feedback**: Optional open-ended feedback from the user.

This data is saved to a CSV file named `pcb_survey_results_<session_id>.csv` in the same directory as the script.
