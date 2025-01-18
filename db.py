import mysql.connector
from mysql.connector import Error

db_config = {
    'host': 'localhost', 
    'user': 'root',       
    'password': '',      
    'database': 'face_recognition' # Your database name
}

def conndb():
    try:
        connection = mysql.connector.connect(**db_config) 
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None
