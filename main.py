import io
import cv2
from flask import Flask, render_template, Response, request, jsonify, send_file
from db import conndb
from flask_cors import CORS
import base64
import mysql.connector
import face_recognition
import numpy as np
from deepface import DeepFace
import time
from ultralytics import YOLO

app = Flask(__name__)
CORS(app)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'face_recognition'
}

camera = None
camera_index = 0
CONFIDENCE_THRESHOLD = 0.6

def get_db_connection():
    """Mendapatkan koneksi ke database."""
    connection = conndb()
    return connection

def get_available_cameras():
    """Mendapatkan daftar kamera yang tersedia."""
    available_cameras = []
    i = 0
    while True:
        cap = cv2.VideoCapture(i)
        if not cap.isOpened():
            break
        available_cameras.append((i, f"Kamera {i}"))
        cap.release()
        i += 1
    return available_cameras

@app.route('/')
def index():
    """Menampilkan halaman utama dengan daftar kamera yang tersedia."""
    available_cameras = get_available_cameras()
    return render_template('index.html', cameras=available_cameras)

@app.route('/add_user', methods=['POST'])
def add_user():
    """Menambahkan pengguna baru ke database."""
    name = request.form['name']
    gender = request.form['gender']
    domicile = request.form['domicile']
    image_file = request.files['image']
    img = image_file.read()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO users (name, gender, domicile, face_image) VALUES (%s, %s, %s, %s)",
        (name, gender, domicile, img)
    )
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'message': 'User added successfully!'})

@app.route('/get_users', methods=['GET'])
def get_users():
    """Mengambil daftar pengguna dari database."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, gender, domicile, face_image FROM users")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    
    users_data = []
    for user in users:
        user_data = {
            'id': user[0],
            'name': user[1],
            'gender': user[2],
            'domicile': user[3],
            'face_image': base64.b64encode(user[4]).decode('utf-8')
        }
        users_data.append(user_data)
    
    return jsonify(users_data)

@app.route('/get_user_image/<int:user_id>', methods=['GET'])
def get_user_image(user_id):
    """Mengambil gambar wajah pengguna berdasarkan ID."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT face_image FROM users WHERE id = %s", (user_id,))
    image_data = cursor.fetchone()
    cursor.close()
    connection.close()

    if image_data:
        return Response(image_data[0], mimetype='image/jpeg')
    else:
        return jsonify({'error': 'User not found'})

@app.route('/video_feed/<int:selected_camera_index>')
def video_feed(selected_camera_index):
    """Mengalirkan video dari kamera yang dipilih."""
    return Response(gen(selected_camera_index), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_image', methods=['POST'])
def capture_image():
    """Menangkap gambar dari kamera dan menyimpannya ke database."""
    data = request.get_json()
    name = data.get('name', 'Unknown')
    gender = data.get('gender', 'Unknown')
    domicile = data.get('domicile', 'Unknown')
    selected_camera_index = int(data.get('selected_camera_index', 0))

    print(f"Received Name: {name} (Type: {type(name)})")
    print(f"Received Gender: {gender} (Type: {type(gender)})")
    print(f"Received Domicile: {domicile} (Type: {type(domicile)})")
    print(f"Selected Camera Index: {selected_camera_index} (Type: {type(selected_camera_index)})")

    if not isinstance(gender, str) or not isinstance(domicile, str):
        return jsonify({'error': 'Gender and Domicile should be strings'}), 400

    camera = cv2.VideoCapture(selected_camera_index)

    if not camera.isOpened():
        return jsonify({'error': f'Failed to open camera with index {selected_camera_index}'})

    time.sleep(1)

    ret, frame = camera.read()
    if not ret:
        camera.release()
        return jsonify({'error': 'Failed to capture image'})

    ret, jpeg = cv2.imencode('.jpg', frame)
    if not ret:
        camera.release()
        return jsonify({'error': 'Failed to encode image'})

    img = jpeg.tobytes()

    print(f"Captured Image Type: {type(img)}")
    print(f"Captured Image Length: {len(img)} bytes")

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (name, gender, domicile, face_image) VALUES (%s, %s, %s, %s)",
            (name, gender, domicile, img)
        )
        connection.commit()
        cursor.close()
        connection.close()

        camera.release()

        return jsonify({'message': 'User and image captured successfully!'})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Failed to save user and image to database'}), 500

@app.route('/upload_user_image', methods=['POST'])
def upload_user_image():
    """Mengunggah gambar pengguna dan menyimpannya ke database."""
    name = request.form['name']
    gender = request.form['gender']
    domicile = request.form['domicile']
    
    image = request.files.get('image')
    if image:
        image_data = image.read()

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (name, gender, domicile, face_image) VALUES (%s, %s, %s, %s)",
            (name, gender, domicile, image_data)
        )
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'User added successfully!'})

    elif 'image' in request.form:
        image_data = request.form['image']

        if image_data.startswith('data:image'):
            try:
                image_data = image_data.split(',')[1]
                image_binary = base64.b64decode(image_data)
            except IndexError:
                return jsonify({'error': 'Invalid image data format'}), 400
        else:
            image_binary = base64.b64decode(image_data)

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (name, gender, domicile, face_image) VALUES (%s, %s, %s, %s)",
            (name, gender, domicile, image_binary)
        )
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'User added successfully!'})

    else:
        return jsonify({'error': 'Image not found!'}), 400

@app.route('/cancel_capture')
def cancel_capture():
    """Membatalkan proses penangkapan gambar."""
    return jsonify({'message': 'capture cancelled'})

@app.route('/debug_table', methods=['GET'])
def debug_table():
    """Menampilkan tabel debug untuk pengguna."""
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    cursor.execute("SELECT id, name, gender, domicile, face_image FROM users")
    users = cursor.fetchall()
    cursor.close()
    connection.close()

    users_data = []
    for user in users:
        if user[4]:
            encoded_image = base64.b64encode(user[4]).decode('utf-8')
        else:
            encoded_image = None

        user_data = {
            'id': user[0],
            'name': user[1],
            'gender': user[2],
            'domicile': user[3],
            'face_image': encoded_image
        }
        users_data.append(user_data)

    return render_template('debug_table.html', users=users_data)

@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Menghapus pengguna berdasarkan ID."""
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message': 'User deleted successfully'})

@app.route('/update_user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Memperbarui data pengguna berdasarkan ID."""
    data = request.get_json()
    name = data['name']
    gender = data['gender']
    domicile = data['domicile']
    
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET name = %s, gender = %s, domicile = %s
        WHERE id = %s
    """, (name, gender, domicile, user_id))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message': 'User updated successfully'})

known_face_encodings = []
known_face_names = []

def load_known_faces_from_db():
    """Memuat wajah yang dikenal dari database."""
    global known_face_encodings, known_face_names
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT id, name, face_image FROM users WHERE face_image IS NOT NULL")
    users = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    for user in users:
        user_id, name, face_image = user

        if face_image:
            try:
                np_img = np.frombuffer(face_image, dtype=np.uint8)
                img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                
                if img is not None:
                    face_encodings = face_recognition.face_encodings(img)
                    
                    if face_encodings:
                        known_face_encodings.append(face_encodings[0])
                        known_face_names.append(name)
                    else:
                        print(f"No faces detected in the image for user {name} (ID: {user_id})")
                else:
                    print(f"Failed to decode the face image for user {name} (ID: {user_id})")
            except Exception as e:
                print(f"Error processing face image for user {name} (ID: {user_id}): {e}")
        else:
            print(f"No face image found for user {name} (ID: {user_id})")

def save_face_encoding_to_db(user_name, image_path):
    """Menyimpan encoding wajah ke database."""
    try:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        
        if not face_encodings:
            print(f"No faces detected in the image: {image_path}")
            return
        
        face_encoding = face_encodings[0]

        face_encoding_bytes = face_encoding.tobytes()
        face_encoding_b64 = base64.b64encode(face_encoding_bytes).decode('utf-8')

        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name, face_encoding) VALUES (%s, %s)",
            (user_name, face_encoding_b64)
        )
        conn.commit()

        print(f"Successfully saved face encoding for {user_name}.")

    except mysql.connector.Error as err:
        print(f"Error inserting into the database: {err}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT name, gender, domicile FROM users WHERE name = %s", (name,))
    users = cursor.fetchall()
    cursor.close()
    connection.close()

    users_data = []
    for user in users:
        user_data = {
            'name': user[0],
            'gender': user[1],
            'domicile': user[2],
            'confidence': confidence
        }
        users_data.append(user_data)

    return jsonify(users_data)

captured_data = {
    "capturedName": "Unknown",
    "confidence": 0.0
}

def gen(selected_camera_index):
    """Menghasilkan frame video dari kamera yang dipilih."""
    global captured_data
    camera = cv2.VideoCapture(selected_camera_index)

    if not camera.isOpened():
        raise RuntimeError(f"Cannot open camera index {selected_camera_index}")

    while True:
        ret, frame = camera.read()
        if not ret:
            break

        rgb_frame = frame[:, :, ::-1]
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        capturedName = "Unknown"
        gender = "Unknown"
        confidence = 0.0

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

            best_match_index = np.argmin(face_distances)
            confidence = 1 - face_distances[best_match_index]

            if confidence >= 0.5 and matches[best_match_index]:
                capturedName = known_face_names[best_match_index]

            gender = predict_gender(frame)

            captured_data['capturedName'] = capturedName
            captured_data['confidence'] = confidence

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.putText(frame, f"{capturedName}", (left + 5, top - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.putText(frame, f"Confidence: {confidence*100:.2f}%", (left + 5, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.putText(frame, f"Gender: {gender}", (left + 5, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            break

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    camera.release()

@app.route('/get_captured_data')
def get_captured_data():
    """Mengambil data yang ditangkap."""
    return jsonify(captured_data)

@app.route('/get_recognized_data')
def get_recognized_data():
    """Mengambil data pengguna yang dikenali."""
    captured_name = captured_data['capturedName']
    confidence = captured_data['confidence']

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT name, gender, domicile FROM users WHERE name = %s", (captured_name,))
    user_data = cursor.fetchone()
    connection.close()

    if user_data:
        name, gender, domicile = user_data
        return jsonify({
            'name': name,
            'gender': gender,
            'domicile': domicile,
            'confidence': f"{confidence*100:.2f}%"
        })
    else:
        return jsonify({
            'error': 'User not found'
        }), 404

def predict_gender(frame):
    """Memprediksi gender dari frame video."""
    try:
        analysis = DeepFace.analyze(frame, actions=['gender'], enforce_detection=False)
        
        gender = analysis[0]['dominant_gender']
        gender_probabilities = analysis[0]['gender']
        
        gender_confidence = gender_probabilities.get(gender.capitalize(), 0)

        if gender_confidence < 50:
            gender = "Unknown"

        return gender
    except Exception as e:
        print(f"Error in gender prediction: {e}")
        return "Unknown"

@app.route('/debug_faces', methods=['GET'])
def debug_faces():
    """Menampilkan wajah yang dikenal untuk debugging."""
    global known_face_names
    return jsonify({"known_faces": known_face_names})

@app.route('/retrain_faces', methods=['POST'])
def retrain_faces():
    """Melatih ulang wajah yang dikenal dari database."""
    load_known_faces_from_db()
    return jsonify({'message': 'Faces retrained successfully!'})

# Load YOLOv8 model
# model = YOLO('yolov8n.pt')

# Load newest model 
model = YOLO('yolo11m.pt')

@app.route('/classify_image', methods=['POST'])
def classify_image():
    """Mengklasifikasikan gambar menggunakan model YOLOv8."""
    image_file = request.files['yoloImage']
    img = image_file.read()

    temp_image_path = 'temp_image.jpg'
    with open(temp_image_path, 'wb') as f:
        f.write(img)

    results = model(temp_image_path, conf=0.5)
    if results:
        result = results[0]
        if result.boxes:
            img = cv2.imread(temp_image_path)
            classifications = []
            for box in result.boxes:
                class_id = int(box.cls)
                name = result.names[class_id]
                confidence = float(box.conf) * 100

                x1, y1, x2, y2 = map(int, [coord for sublist in box.xyxy.tolist() for coord in sublist])

                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img, f"{name} {confidence:.2f}%", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                classifications.append({'name': name, 'confidence': confidence})

            _, buffer = cv2.imencode('.jpg', img)
            image_base64 = base64.b64encode(buffer).decode('utf-8')

            return jsonify({'classifications': classifications, 'image': image_base64})
        else:
            return jsonify({'error': 'No objects detected'}), 500
    else:
        return jsonify({'error': 'Classification failed'}), 500
    
import math

def gen_car_count_feed():
    cap = cv2.VideoCapture("http://103.95.42.254:84/mjpg/video.mjpg?camera=1&timestamp=1739522088479")
    if not cap.isOpened():
        raise RuntimeError("Cannot open the public camera stream")

    vehicle_count = 0
    prev_centers = []  # List of [center_x, center_y] from previous frame
    DIST_THRESHOLD = 50  # Distance threshold in pixels

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        height, width = frame.shape[:2]

        # Define a horizontal detection band between blue lines
        y_top = int(0.4 * height)
        y_bottom = int(0.6 * height)
        roi_boxes = [(0, y_top, width, y_bottom)]
        for (rx1, ry1, rx2, ry2) in roi_boxes:
            cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (255, 0, 255), 2)  # Magenta box

        results = model(frame, conf=0.25)
        current_centers = []
        new_detections = 0

        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls)
                    label = result.names[class_id].lower()
                    if label in ["bus", "truck", "car", "motorcycle"]:
                        xy = box.xyxy.tolist()[0]
                        x1, y1, x2, y2 = map(int, xy)
                        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

                        # Check if center is within detection band
                        if any(ry1 <= center_y <= ry2 for (_, ry1, _, ry2) in roi_boxes):
                            duplicate = False
                            for prev_center in prev_centers:
                                distance = math.hypot(center_x - prev_center[0], center_y - prev_center[1])
                                if distance < DIST_THRESHOLD:
                                    duplicate = True
                                    break
                            if not duplicate:
                                new_detections += 1
                            current_centers.append([center_x, center_y])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                            cv2.putText(frame, f"{label} {box.conf[0]:.2f}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        vehicle_count += new_detections
        prev_centers = current_centers[:]

        cv2.putText(frame, f"Vehicle Count: {vehicle_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            break

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    cap.release()

@app.route('/car_count_feed')
def car_count_feed():
    return Response(gen_car_count_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Optional: New route to render the car count page
@app.route('/car_count')
def car_count():
    return render_template('car_count.html')

if __name__ == '__main__':
    print("Loading known faces from the database...")
    load_known_faces_from_db()
    app.run(debug=True)
