import mysql.connector
import sys

# Passwords to test
passwords = ["", "root", "password", "1234", "admin", "123456", "mysql", "toor"]

# Hosts to test
hosts = ["localhost", "127.0.0.1"]

print("Testing common MySQL passwords...")

for host in hosts:
    print(f"\n--- Testing Host: {host} ---")
    for pwd in passwords:
        try:
            print(f"Testing root:{pwd}@{host} ...", end=" ")
            conn = mysql.connector.connect(
                host=host,
                user="root",
                password=pwd
            )
            if conn.is_connected():
                print("SUCCESS!")
                print(f"\nFOUND IT! Use these credentials:")
                print(f"Host: {host}")
                print(f"User: root")
                print(f"Password: {pwd}")
                conn.close()
                sys.exit(0)
        except mysql.connector.Error as err:
            print(f"Failed ({err.errno})")

print("\nCould not find the password. Please check your MySQL installation.")
sys.exit(1)
