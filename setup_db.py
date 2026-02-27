import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    connection = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='',
    )
    
    cursor = connection.cursor()
    
    # Create database
    cursor.execute("CREATE DATABASE IF NOT EXISTS taskmanager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("✅ Database 'taskmanager' created successfully!")
    
    cursor.close()
    connection.close()
    
except mysql.connector.Error as err:
    if err.errno == 2003:
        print("❌ Error: Could not connect to MySQL server.")
        print("   Make sure MySQL is running on localhost:3306")
    else:
        print(f"❌ Error: {err}")

