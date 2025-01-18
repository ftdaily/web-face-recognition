
## 🚀 About Me
I'm a student at Gunadarma University. Mainly work on game modding, reverse engineering, backend development, and other tech-related tasks.

-*mfarrellr*

# Web Based Face Recognition - CRUD

A Simple Web-Based Face Recognition System with CRUD functionality allows users to upload, store, update, and delete facial images, while also enabling face recognition for retrieving and displaying previously stored data. 

The system uses a webcam to capture facial images, processes them for recognition, and then associates the recognized face with relevant data from a database. The implementation supports seamless interaction with the backend, enabling users to manage images and access personalized data based on facial recognition, ensuring both dynamic data management and secure authentication.
## Features

- **Access to Webcams and Uploading Images**  
  Users have two options for adding data: manually uploading photographs or using the webcam to take facial images.

- **Automatic Recognition of Faces**  
  The system can automatically identify faces (you may disable this capability if necessary) and obtain the person's associated data.

- **Modify/Remove Database Records**  
  The database's entries can be edited or removed by users, which is helpful for debugging.

- **Prediction of Gender**  
  The algorithm uses the captured face to try to guess the person's gender. Please be aware that because it makes use of the DeepFace library, this could not be entirely correct.



---

### Extra Features

- **The ability to recognize faces**
   automatically recognizes faces and compares them to the database's recorded information to identify them. If desired, this can be toggled to manual.

- **CRUD Processes on User Information**  
   enables users to manage the system's database by performing CRUD (Create, Read, Update, Delete) actions on user data, including facial photos.

- **Collaboration with Databases**  
   The application stores user data and facial photos by connecting to a MySQL database. From the program, users can add, edit, or remove records.

- **Flask for the backend**  
    driven by Flask, a Python web framework that manages database operations and face recognition backend processing.
## Frontend Libraries & Frameworks

- **JavaScript**: Used for frontend functionality, such as real-time webcam access and face recognition logic.

- **Bootstrap**: A popular open-source CSS framework used for building responsive, mobile-first web pages.  
  CDN link: [Bootstrap 5.3.0-alpha1](https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css)
  
- **Popper.js**: A JavaScript library used for managing popups, tooltips, and other UI elements in conjunction with Bootstrap.  
  CDN link: [Popper.js 2.11.6](https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js)

- **jQuery**: A fast, small, and feature-rich JavaScript library used for DOM manipulation, event handling, and AJAX interactions.  
  CDN link: [jQuery 3.6.0](https://code.jquery.com/jquery-3.6.0.min.js)

## Backend

- **Python**: The primary programming language used for backend processing and facial recognition tasks.
- **Flask**: Python framework for the backend API.
- **OpenCV**: For accessing the webcam and performing facial image processing.
- **Face Recognition**: A library that recognizes and processes faces, connecting them to stored user data.

## Database

- **MySQL**: To store user data and facial images in the database.
# Run Locally

Before proceeding, I would recommend setting up a virtual environment to avoid any conflicts between libraries and Python versions.
```
conda create -n .condaEnv310 python=3.10
```

If you have an active environment, deactivate it first by running.
```
conda deactivate
```

Next, activate the created environment.
```
conda activate .condaEnv310
```

To check if you are using the correct environment.
```
conda info --envs
```
This will list all your conda environments and highlight the active one with an asterisk (*).


## Creating the Database and Running the Program

Ensure that the crud database is created in your database management system (DBMS).

```bash
CREATE DATABASE face_recognition;
```

Create the table.
```
CREATE TABLE users (
    id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
    gender VARCHAR(10) COLLATE utf8mb4_general_ci DEFAULT NULL,
    domicile VARCHAR(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
    face_image LONGBLOB DEFAULT NULL
);

```

Clone the project.

```bash
git clone https://github.com/ftdaily/web-face-recognition
```

Go to the project directory.

```bash
cd web-face-recognition.
```

Install dependencies.
```bash
pip install -r requirements.txt
```

Start the server.
```
python cleaned-app.py
```

# License

[MIT](https://choosealicense.com/licenses/mit/)

