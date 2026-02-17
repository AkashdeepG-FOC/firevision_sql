import mysql.connector
import sys

pwd = "" # Empty password
print(f"Testing connectivity to 'firevision' with empty password...")

try:
    # 1. Connect to Server (no DB)
    conn = mysql.connector.connect(host="localhost", user="root", password=pwd)
    if conn.is_connected():
        print("SUCCESS! Connected to MySQL Server with empty password.")
        cursor = conn.cursor()
        
        # 2. Check Database
        db_name = "firevision"
        try:
            conn.database = db_name
            print(f"SUCCESS! Database '{db_name}' exists and is accessible with empty password.")
        except mysql.connector.Error as err:
            if err.errno == 1049: # Unknown database
                print(f"Database '{db_name}' does not exist. Creating...")
                cursor.execute(f"CREATE DATABASE {db_name}")
                print(f"SUCCESS! Created database '{db_name}' with empty password.")
                conn.database = db_name
            else:
                print(f"FAILED to access database '{db_name}': {err}")
                sys.exit(1)
        
        conn.close()
        sys.exit(0)
    else:
        print("FAILED: Could not connect to MySQL Server with empty password.")
        sys.exit(1)

except mysql.connector.Error as err:
    print(f"FAILED: Connection Error ({err.errno}): {err.msg}")
    sys.exit(1)
