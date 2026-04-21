# Biometric Attendance Platform

A full-featured, AI-powered Biometric Attendance System built with Flask. This platform provides a comprehensive and secure facial recognition-based attendance solution with separate portals for students and teachers, dynamic dashboards, and Google OAuth integration.

## Features

### Student Portal
* **Registration & Login**: Students can register using their details and capture their face directly via webcam. Supports Google OAuth for quick sign-in.
* **Mark Attendance**: Face verification using an external facial recognition model via a web API.
* **Student Dashboard**: Track personal attendance history, total subjects attended, and filter records by specific subjects or dates.
* **Profile Management**: Update personal details like phone number, address, and blood group.

### Teacher Portal
* **Teacher Signup & Login**: Secure access for educators (Google OAuth supported).
* **Teacher Dashboard**: High-level overview showing today's total check-ins and recent system-wide attendance logs.
* **Mark Attendance**: Teachers can also manually trigger the facial recognition attendance system for students.
* **Attendance Records**: Advanced filtering by Name, Date, and Subject.
* **Export Data**: One-click export of all attendance records to a CSV file.
* **View Registered Students**: View the list of all students currently registered with facial data in the system.

### Core System Architecture
* **Facial Recognition Backend**: Offloads heavy facial recognition (using `face_recognition` and OpenCV) to an external Google Colab/ngrok API.
* **Local Storage**: Lightweight storage using `students.json` and `teachers.json` for credentials, and `attendance.csv` for attendance tracking.
* **Ajax-Based Check-ins**: Smooth, page-reload-free attendance marking.
* **Liveness & Visual Feedback**: The frontend is built to show the camera feed seamlessly.

## Project Structure

```text
mini/
│
├── app.py                 # Main Flask Application (Routes, Auth, Dashboards)
├── train.py               # Model Training/Evaluation API (Meant for Colab/Backend)
├── .env                   # Environment variables (Google Client ID, etc.)
├── .gitignore             # Ignored files
├── attendance.csv         # Database for attendance logs
├── students.json          # Student authentication database
├── teachers.json          # Teacher authentication database
├── static/                
│   ├── students/          # Stored student profile/face images
│   ├── style.css          # Global Stylesheet
│   └── face_logic.js      # Frontend camera and face detection logic
└── templates/             # HTML Templates (Dashboards, Login, Register, etc.)
```

## Getting Started

### Prerequisites

You will need Python 3.8+ installed on your system.

### 1. Install Dependencies

Install the required Python packages for the web server:

```bash
pip install flask pandas requests python-dotenv google-auth
```

### 2. Environment Variables

Create a `.env` file in the root directory (if it doesn't exist) and add your Google OAuth Client ID to enable Google Login:

```env
GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
```

### 3. Setup Facial Recognition API (Backend)

Because facial recognition is computationally heavy, this app is designed to offload the recognition to an external API (like a Google Colab notebook). 

1. Ensure the backend API (running `train.py` or equivalent Colab script with `face_recognition`, `opencv-python`, etc.) is running.
2. If using Colab and `ngrok`, copy the generated public ngrok URL.
3. Open `app.py` and update the `COLAB_API` variable to point to your active recognition server:
   ```python
   COLAB_API = "https://your-ngrok-url.ngrok-free.dev/"
   ```

*(Note: Every time the app starts, it automatically syncs the registered student faces in `static/students/` to the Colab API in a background thread.)*

### 4. Run the Application

Start the Flask server:

```bash
python app.py
```

The application will be accessible at: **http://127.0.0.1:5000**

## How to Use

1. **First-Time Setup**: Go to the web app, choose **Register** and sign up as a student. Ensure your camera is working to capture the initial face data. 
2. **Marking Attendance**: After registering, log in as a student (or teacher), navigate to the **Mark Attendance** section, select the Subject and Mode (Entry/Exit), and capture your face. The app will communicate with the external API to verify identity and update `attendance.csv`.
3. **Teacher Controls**: Teachers can log in to view all system-wide attendance, search for specific students, and export the logs directly to their machine.
