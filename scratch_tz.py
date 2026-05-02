import mysql.connector
from datetime import datetime

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'bd_pisid'
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT NOW() as db_time")
    row = cursor.fetchone()
    print("Database NOW():", row['db_time'])
    print("Python NOW():", datetime.now())
    
    cursor.execute("SELECT * FROM Simulacao WHERE Ativo = TRUE")
    sim = cursor.fetchone()
    print("Active Simulation:", "Yes" if sim else "No")
    
    conn.close()
except Exception as e:
    print(e)
