# from flask import Flask, render_template, request
# import os, base64, requests
# import pandas as pd
# from datetime import datetime

# app = Flask(__name__)

# COLAB_API = "https://unicursal-pseudoconservatively-trinidad.ngrok-free.dev/"

# os.makedirs("static/students", exist_ok=True)

# # ---------- ROUTES ----------

# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/register", methods=["GET","POST"])
# def register():
#     if request.method == "POST":
#         name = request.form["name"]
#         usn = request.form["usn"]
#         image = request.form["image"]

#         path = f"static/students/{usn}_{name}.jpg"
#         save_image(image, path)

#         send_students_to_colab()

#         return f"{name} registered!"

#     return render_template("register.html")


# @app.route("/attendance", methods=["GET","POST"])
# def attendance():
#     if request.method == "POST":
#         image = request.form["image"]

#         res = requests.post(f"{COLAB_API}/recognize", json={"image": image})
#         result = res.json()

#         if result["status"] == "success":
#             name = result["name"]
#             mark_attendance(name)
#             return f"Marked: {name}"

#         return "Unknown"

#     return render_template("attendance.html")


# @app.route("/dashboard")
# def dashboard():
#     # 1. Get Attendance Data
#     attendance_data = []
#     if os.path.exists("attendance.csv") and os.path.getsize("attendance.csv") > 0:
#         df = pd.read_csv("attendance.csv")
#         attendance_data = df.to_dict(orient="records")

#     # 2. Get Registered Students Data from filenames
#     registered_students = []
#     for file in os.listdir("static/students"):
#         if file.endswith(".jpg"):
#             parts = file.replace(".jpg", "").split("_")
#             if len(parts) == 2:
#                 registered_students.append({
#                     "usn": parts[0],
#                     "name": parts[1],
#                     "photo": file
#                 })

#     return render_template("dashboard.html", 
#                            attendance=attendance_data, 
#                            students=registered_students)


# # ---------- HELPERS ----------

# def save_image(data, path):
#     img = base64.b64decode(data.split(',')[1])
#     with open(path, 'wb') as f:
#         f.write(img)


# def send_students_to_colab():
#     students = []

#     for file in os.listdir("static/students"):
#         path = os.path.join("static/students", file)

#         with open(path, "rb") as f:
#             img_base64 = base64.b64encode(f.read()).decode()

#         usn = file.split("_")[0]
#         name = file.split("_")[1].split(".")[0]

#         students.append({
#             "name": name,
#             "usn": usn,
#             "image": "data:image/jpeg;base64," + img_base64
#         })

#     try:
#         requests.post(f"{COLAB_API}/load", json={"students": students})
#     except:
#         print("Colab sync failed")


# import pandas as pd
# import os
# from datetime import datetime

# def mark_attendance(name):
#     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     new_row = pd.DataFrame([[name, now]], columns=["Name", "Time"])

#     # File doesn't exist OR empty → create fresh
#     if not os.path.exists("attendance.csv") or os.path.getsize("attendance.csv") == 0:
#         new_row.to_csv("attendance.csv", index=False)
#         return

#     try:
#         old = pd.read_csv("attendance.csv")
#     except:
#         new_row.to_csv("attendance.csv", index=False)
#         return

#     if name in old["Name"].values:
#         return

#     updated = pd.concat([old, new_row], ignore_index=True)
#     updated.to_csv("attendance.csv", index=False)


# # ---------- RUN ----------

# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, render_template, request, session, redirect, jsonify, send_file
import os, base64, requests, json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecret123"

COLAB_API = "https://unicursal-pseudoconservatively-trinidad.ngrok-free.dev/"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

os.makedirs("static/students", exist_ok=True)

# ===========================
# 📂 STORAGE (JSON)
# ===========================

def load_data(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)


from functools import wraps
import threading

# ===========================
# 🛡️ DECORATORS
# ===========================

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "student" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "teacher" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# ===========================

@app.route("/")
def home():
    if "student" in session:
        return redirect("/student/dashboard")
    if "teacher" in session:
        return redirect("/teacher/dashboard")
    return redirect("/login")

@app.route("/login")
def login():
    return render_template("login.html", google_client_id=GOOGLE_CLIENT_ID, hide_sidebar=True)

@app.route("/choose-register")
def choose_register():
    return render_template("choose_register.html", hide_sidebar=True)


# ===========================
# 👨‍🎓 STUDENT REGISTER
# ===========================

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        usn = request.form["usn"]
        email = request.form["email"]
        password = request.form["password"]
        image = request.form["image"]

        # Save face
        path = f"static/students/{usn}_{name}.jpg"
        save_image(image, path)

        # Save student auth
        students = load_data("students.json")
        students.append({
            "name": name,
            "usn": usn,
            "email": email,
            "password": password
        })
        save_data("students.json", students)

        send_students_to_colab()

        return redirect("/login")

    return render_template("register.html", hide_sidebar=True)


# ===========================
# 👨‍🎓 STUDENT LOGIN
# ===========================

@app.route("/student/login", methods=["GET","POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        students = load_data("students.json")

        for s in students:
            if s["email"] == email and s["password"] == password:
                session["student"] = s
                return redirect("/student/dashboard")

        return "Invalid credentials"

    return render_template("student_login.html", google_client_id=GOOGLE_CLIENT_ID)


# ===========================
# 👨‍🎓 STUDENT DASHBOARD
# ===========================

@app.route("/google-login", methods=["POST"])
def google_login():
    token = request.json.get("credential")
    role = request.json.get("role", "student")
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo['email']
        name = idinfo.get('name', 'Google User')

        teachers = load_data("teachers.json")
        for t in teachers:
            if t.get("email") == email:
                session["teacher"] = t
                return jsonify({"status": "success", "redirect": "/teacher/dashboard"})
                
        students = load_data("students.json")
        for s in students:
            if s.get("email") == email:
                session["student"] = s
                return jsonify({"status": "success", "redirect": "/student/dashboard"})
        
        if role == "teacher":
            new_user = {"name": name, "email": email, "password": ""}
            teachers.append(new_user)
            save_data("teachers.json", teachers)
            session["teacher"] = new_user
            return jsonify({"status": "success", "redirect": "/teacher/dashboard"})
        else:
            new_user = {"name": name, "email": email, "usn": "N/A", "password": ""}
            students.append(new_user)
            save_data("students.json", students)
            session["student"] = new_user
            return jsonify({"status": "success", "redirect": "/student/dashboard"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/student/dashboard")
@student_required
def student_dashboard():
    student = session["student"]
    attendance_data = []
    total_attended = 0
    total_subjects = 0

    if os.path.exists("attendance.csv") and os.path.getsize("attendance.csv") > 0:
        df = pd.read_csv("attendance.csv")
        
        if "Subject" not in df.columns:
            df["Subject"] = "General"

        # Apply Filters
        subj_filter = request.args.get("subject")
        date_filter = request.args.get("date")
        
        student_df = df[df["Name"] == student["name"]]
        
        # Calculate stats BEFORE filtering
        total_attended = len(student_df[student_df["Mode"] == "Entry"])
        total_subjects = student_df[student_df["Mode"] == "Entry"]["Subject"].nunique()

        if subj_filter and subj_filter != "All":
            student_df = student_df[student_df["Subject"] == subj_filter]
        if date_filter:
            student_df = student_df[student_df["Date"] == date_filter]
            
        attendance_data = student_df.to_dict(orient="records")

    return render_template("student_dashboard.html",
                           student=student,
                           attendance=attendance_data,
                           total_attended=total_attended,
                           total_subjects=total_subjects)


@app.route("/student/profile", methods=["GET", "POST"])
@student_required
def student_profile():
    student = session["student"]
    
    if request.method == "POST":
        phone = request.form.get("phone", "")
        address = request.form.get("address", "")
        blood_group = request.form.get("blood_group", "")
        
        students = load_data("students.json")
        for s in students:
            if s["email"] == student["email"]:
                s["phone"] = phone
                s["address"] = address
                s["blood_group"] = blood_group
                session["student"] = s
                break
        save_data("students.json", students)
        return redirect("/student/profile")
        
    return render_template("student_profile.html", student=student)

# ===========================
# 👨‍🏫 TEACHER SIGNUP
# ===========================

@app.route("/teacher/signup", methods=["GET","POST"])
def teacher_signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        teachers = load_data("teachers.json")
        teachers.append({
            "name": name,
            "email": email,
            "password": password
        })
        save_data("teachers.json", teachers)

        return redirect("/teacher/login")

    return render_template("teacher_signup.html")


# ===========================
# 👨‍🏫 TEACHER LOGIN
# ===========================

@app.route("/teacher/login", methods=["GET","POST"])
def teacher_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        teachers = load_data("teachers.json")

        for t in teachers:
            if t["email"] == email and t["password"] == password:
                session["teacher"] = t
                return redirect("/teacher/dashboard")

        return "Invalid credentials"

    return render_template("teacher_login.html", google_client_id=GOOGLE_CLIENT_ID)


# ===========================
# 👨‍🏫 TEACHER DASHBOARD
# ===========================


# ----------------------------
# TEACHER DASHBOARD (HOME)
# ----------------------------
@app.route("/teacher/dashboard")
@teacher_required
def teacher_dashboard():
    teacher = session["teacher"]
    recent_logs = []
    today_checkins = 0

    if os.path.exists("attendance.csv") and os.path.getsize("attendance.csv") > 0:
        df = pd.read_csv("attendance.csv")
        
        if "Subject" not in df.columns:
            df["Subject"] = "General"

        # Quick daily summary
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_checkins = len(df[(df["Date"] == today_str) & (df["Mode"] == "Entry")])

        recent_logs = df.tail(15).to_dict(orient="records")

    return render_template("teacher_dashboard.html", teacher=teacher, recent_logs=recent_logs, today_checkins=today_checkins)

@app.route("/export-csv")
@teacher_required
def export_csv():
    if os.path.exists("attendance.csv"):
        return send_file("attendance.csv", as_attachment=True, download_name=f"attendance_export_{datetime.now().strftime('%Y%m%d')}.csv")
    return "No records to export"


# ----------------------------
# MARK ATTENDANCE PAGE
# ----------------------------
@app.route("/teacher/mark", methods=["GET", "POST"])
@teacher_required
def teacher_mark():
    if request.method == "POST":
        image = request.form["image"]
        mode = request.form.get("mode", "Entry")
        subject = request.form.get("subject", "General")

        try:
            res = requests.post(f"{COLAB_API}/recognize", json={"image": image})
            result = res.json()

            if result["status"] == "success":
                name = result["name"]
                
                students = load_data("students.json")
                usn = "N/A"
                for s in students:
                    if s.get("name") == name:
                        usn = s.get("usn", "N/A")
                        break

                mark_attendance(name, mode, subject)
                return jsonify({"status": "success", "name": name, "usn": usn, "message": f"{mode} marked for {subject}"})

            return jsonify({"status": "error", "message": "Face not recognized"})

        except:
            return jsonify({"status": "error", "message": "API error"})

    return render_template("teacher_mark.html")


# ----------------------------
# RECORDS PAGE (ATTENDANCE)
# ----------------------------
@app.route("/teacher/records")
@teacher_required
def teacher_records():
    attendance_data = []

    if os.path.exists("attendance.csv") and os.path.getsize("attendance.csv") > 0:
        df = pd.read_csv("attendance.csv")

        # Ensure Date column
        if "Date" not in df.columns:
            df["Date"] = pd.to_datetime(df["Time"]).dt.date.astype(str)

        # Name Search
        search_name = request.args.get("name", "").lower()
        if search_name:
            df = df[df["Name"].str.lower().str.contains(search_name)]

        # Date Filter
        date_filter = request.args.get("date")
        if date_filter:
            df = df[df["Date"] == date_filter]

        # Sort by Date desc
        df = df.sort_values(by="Date", ascending=False)
        attendance_data = df.to_dict(orient="records")

    return render_template(
        "teacher_records.html",
        attendance=attendance_data,
        current_date=request.args.get("date", "")
    )

# ----------------------------
# REGISTERED STUDENTS PAGE
# ----------------------------
@app.route("/teacher/students")
@teacher_required
def teacher_students():
    students = []
    if os.path.exists("static/students"):
        for file in os.listdir("static/students"):
            if file.endswith(".jpg"):
                parts = file.replace(".jpg", "").split("_")
                if len(parts) == 2:
                    students.append({
                        "usn": parts[0],
                        "name": parts[1],
                        "photo": file
                    })

    return render_template("teacher_students.html", students=students)


# ----------------------------
# LOGOUT
# ----------------------------
@app.route("/teacher/logout")
def teacher_logout():
    session.pop("teacher", None)
    return redirect("/login")

@app.route("/student/logout")
def student_logout():
    return redirect("/login")

# ===========================
# 🕒 ATTENDANCE (ENTRY/EXIT)
# ===========================

@app.route("/attendance", methods=["GET","POST"])
@student_required
def attendance():
    if request.method == "POST":
        image = request.form["image"]
        mode = request.form.get("mode", "Entry")
        subject = request.form.get("subject", "General")

        try:
            res = requests.post(f"{COLAB_API}/recognize", json={"image": image})
            result = res.json()

            if result["status"] == "success":
                name = result["name"]
                
                students = load_data("students.json")
                usn = "N/A"
                for s in students:
                    if s.get("name") == name:
                        usn = s.get("usn", "N/A")
                        break
                        
                mark_attendance(name, mode, subject)
                return jsonify({"status": "success", "name": name, "usn": usn, "message": f"{mode} marked for {subject}"})

            return jsonify({"status": "error", "message": "Unknown Face"})
            
        except:
            return jsonify({"status": "error", "message": "API error"})

    return render_template("attendance.html")

@app.route('/evaluate', methods=['GET'])
def evaluate():
    return jsonify(evaluate_model())


# ===========================
# 📊 GENERAL DASHBOARD (UNCHANGED)
# ===========================

@app.route("/dashboard")
def dashboard():
    attendance_data = []

    if os.path.exists("attendance.csv") and os.path.getsize("attendance.csv") > 0:
        try:
            df = pd.read_csv("attendance.csv")
            attendance_data = df.to_dict(orient="records")
        except:
            attendance_data = []

    registered_students = []
    for file in os.listdir("static/students"):
        if file.endswith(".jpg"):
            parts = file.replace(".jpg", "").split("_")
            if len(parts) == 2:
                registered_students.append({
                    "usn": parts[0],
                    "name": parts[1],
                    "photo": file
                })

    return render_template("dashboard.html",
                           attendance=attendance_data,
                           students=registered_students)


# ===========================
# 🧠 HELPERS
# ===========================

def save_image(data, path):
    img = base64.b64decode(data.split(',')[1])
    with open(path, 'wb') as f:
        f.write(img)


def send_students_to_colab():
    students = []

    for file in os.listdir("static/students"):
        path = os.path.join("static/students", file)

        with open(path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()

        usn = file.split("_")[0]
        name = file.split("_")[1].split(".")[0]

        students.append({
            "name": name,
            "usn": usn,
            "image": "data:image/jpeg;base64," + img_base64
        })

    try:
        requests.post(f"{COLAB_API}/load", json={"students": students})
    except:
        print("Colab sync failed")


# ===========================
# 🕒 ATTENDANCE STORAGE
# ===========================

def mark_attendance(name, mode, subject="General"):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    new_row = pd.DataFrame([[name, date, time, mode, subject]],
                           columns=["Name", "Date", "Time", "Mode", "Subject"])

    if not os.path.exists("attendance.csv") or os.path.getsize("attendance.csv") == 0:
        new_row.to_csv("attendance.csv", index=False)
        return

    try:
        old = pd.read_csv("attendance.csv")
    except:
        new_row.to_csv("attendance.csv", index=False)
        return

    if "Subject" not in old.columns:
        old["Subject"] = "General"

    updated = pd.concat([old, new_row], ignore_index=True)
    updated.to_csv("attendance.csv", index=False)


# ===========================
# 🚀 RUN
# ===========================

def startup_sync():
    print("Starting initial Colab sync...")
    send_students_to_colab()
    print("Initial Colab sync finished.")

if __name__ == "__main__":
    threading.Thread(target=startup_sync, daemon=True).start()
    app.run(debug=True)