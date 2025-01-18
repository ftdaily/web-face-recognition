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
    connection = conndb()  
    return connection

def get_available_cameras():
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
    available_cameras = get_available_cameras()
    return render_template('index.html', cameras=available_cameras)

@app.route('/add_user', methods=['POST'])
def add_user():
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
    return Response(gen(selected_camera_index), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_image', methods=['POST'])
def capture_image():
    data = request.get_json()
    name = data.get('name', 'Unknown')
    gender = data.get('gender', 'Unknown')
    domicile = data.get('domicile', 'Unknown')
    selected_camera_index = int(data.get('selected_camera_index', 0))  

    # Debug: Log the received data types
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

    # Debug: Log the type and size of the image data
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

        return jsonify({'message': 'User added!'})

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

        return jsonify({'message': 'User added!'})

    else:
        return jsonify({'error': 'Image not found!'}), 400

#Probably unused, but keep it here.
@app.route('/cancel_capture')
def cancel_capture():
    return jsonify({'message': 'capture cancelled'})


################################################################################################

# FOR DEBUGGING PURPOSE

@app.route('/debug_table', methods=['GET'])
def debug_table():
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
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message': 'User deleted successfully'})

@app.route('/update_user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
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


################################################################################################

# TODO: BRUHH

known_face_encodings = []
known_face_names = []

def load_known_faces_from_db():
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
    return jsonify(captured_data)

@app.route('/get_recognized_data')
def get_recognized_data():
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
    global known_face_names
    return jsonify({"known_faces": known_face_names})


@app.route('/retrain_faces', methods=['POST'])
def retrain_faces():
    load_known_faces_from_db()
    return jsonify({'message': 'Faces retrained successfully!'})

################################################################################################ 
if __name__ == '__main__':
    print("Loading known faces from the database...")
    load_known_faces_from_db()
    app.run(debug=True)
