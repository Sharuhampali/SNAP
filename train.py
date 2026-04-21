from flask import Flask, request, jsonify
import face_recognition
import numpy as np
import base64
import cv2
from sklearn.model_selection import train_test_split

app = Flask(__name__)

# =========================
# STORAGE
# =========================
train_encodings = []
train_names = []
train_usn = []

test_encodings = []
test_names = []
test_usn = []

# =========================
# LOAD ROUTE
# =========================
@app.route('/load', methods=['POST'])
def load_faces():
    global train_encodings, train_names, train_usn
    global test_encodings, test_names, test_usn

    train_encodings.clear()
    train_names.clear()
    train_usn.clear()
    test_encodings.clear()
    test_names.clear()
    test_usn.clear()

    data = request.json

    all_encodings = []
    all_names = []
    all_usn = []

    for student in data["students"]:
        try:
            img_data = base64.b64decode(student["image"].split(',')[1])
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            enc = face_recognition.face_encodings(img)

            if len(enc) > 0:
                all_encodings.append(enc[0])
                all_names.append(student["name"])
                all_usn.append(student["usn"])

        except Exception as e:
            print("Error:", str(e))

    if len(all_encodings) < 2:
        return jsonify({"status": "error", "message": "Not enough data"}), 400

    X_train, X_test, y_train, y_test, usn_train, usn_test = train_test_split(
        all_encodings, all_names, all_usn,
        test_size=0.2,
        random_state=42
    )

    train_encodings[:] = X_train
    train_names[:] = y_train
    train_usn[:] = usn_train

    test_encodings[:] = X_test
    test_names[:] = y_test
    test_usn[:] = usn_test

    return jsonify({
        "status": "loaded",
        "train_count": len(train_names),
        "test_count": len(test_names)
    })


# =========================
# EVALUATE ROUTE
# =========================
@app.route('/evaluate', methods=['GET'])
def evaluate():
    correct = 0
    total = len(test_encodings)

    false_positive = 0
    false_negative = 0

    if total == 0:
        return jsonify({"status": "error", "message": "No test data"})

    for i, enc in enumerate(test_encodings):

        distances = face_recognition.face_distance(train_encodings, enc)

        if len(distances) == 0:
            continue

        best_match_index = np.argmin(distances)

        if distances[best_match_index] < 0.5:
            predicted_name = train_names[best_match_index]
        else:
            predicted_name = "unknown"

        actual_name = test_names[i]

        if predicted_name == actual_name:
            correct += 1
        else:
            if predicted_name == "unknown":
                false_negative += 1
            else:
                false_positive += 1

    accuracy = correct / total if total > 0 else 0

    return jsonify({
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "false_positive": false_positive,
        "false_negative": false_negative
    })


# =========================
# 🔥 MAIN EXECUTION (JUPYTER / SCRIPT)
# =========================
if __name__ == "__main__":

    # 👉 TODO: replace this with your actual dataset
    sample_data = {
        "students": [
            # Example format:
            # {
            #     "name": "John",
            #     "usn": "001",
            #     "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ..."
            # }
        ]
    }

    with app.test_client() as client:

        # 🔥 STEP 1: LOAD DATA
        res1 = client.post('/load', json=sample_data)
        print("LOAD RESPONSE:", res1.json)

        # 🔥 STEP 2: EVALUATE
        res2 = client.get('/evaluate')
        print("EVALUATION RESULT:", res2.json)

