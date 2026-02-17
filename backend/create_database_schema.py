import mysql.connector
from backend.core.config import settings

def create_database():
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = connection.cursor()
        
        # Create database
        db_name = "firevision"
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' created or already exists.")
        
        cursor.close()
        connection.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    create_database()
