import mysql.connector as mariadb
from mysql.connector import Error
import sys  # Essential for receiving arguments from PHP

# --- Database Configurations ---
usermysql, passmysql, hostmysql, database = "root", "root", "localhost", "bd_pisid"
nuvemuser, nuvempass, nuvemhost, nuvemDb = "aluno", "aluno", "194.210.86.10", "maze"

# --- Capture Arguments from PHP ---
# Expecting: python script.py IDSimulacao outliers_temp outliers_som alerta_temp_h alerta_temp_l alerta_som time_fechar ruido_limite
try:
    # sys.argv[0] is the script name, so we start at index 1
    php_vars = {
        "id_sim": sys.argv[1],
        "out_temp": sys.argv[2],
        "out_som": sys.argv[3],
        "al_temp_h": sys.argv[4],
        "al_temp_l": sys.argv[5],
        "al_som": sys.argv[6],
        "t_fechar": sys.argv[7],
        "ruido_lim": sys.argv[8]
    }
except IndexError:
    print("Error: Missing arguments from PHP.")
    sys.exit(1)

try:
    # Local Connection
    connection = mariadb.connect(host=hostmysql, user=usermysql, passwd=passmysql,
                                 db=database, connect_timeout=1000, autocommit=True)
    # Cloud Connection
    connection_nuvem = mariadb.connect(host=nuvemhost, user=nuvemuser, passwd=nuvempass,
                                       db=nuvemDb, connect_timeout=1000, autocommit=True)

    cursor_local = connection.cursor()
    cursor_nuvem = connection_nuvem.cursor(dictionary=True)

    # 1. MIGRATE SetupMaze (Your existing logic)
    cursor_nuvem.execute("SELECT * FROM SetupMaze")
    setup_records = cursor_nuvem.fetchall()
    for row in setup_records:
        sql_insert_setup = """INSERT INTO SetupMaze (NumberRooms, NumberMarsamis, NumberPlayers,
                                                     NormalTemperature, TemperatureVarHighToleration, \
                                                     TemperatureVarLowToleration,
                                                     NormalNoise, NoiseVarToleration) \
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor_local.execute(sql_insert_setup, (row['numberrooms'], row['numbermarsamis'], row['numberplayers'],
                                                row['normaltemperature'], row['temperaturevarhightoleration'],
                                                row['temperaturevarlowtoleration'], row['normalnoise'],
                                                row['noisevartoleration']))

    # 2. MIGRATE Corridor Table
    print("Migrating Corridors...")
    cursor_nuvem.execute("SELECT RoomA, RoomB FROM Corridor")
    corridor_records = cursor_nuvem.fetchall()
    for row in corridor_records:
        # Assuming your local Corridor table has columns RoomA and RoomB
        sql_insert_corridor = "INSERT INTO Corridor (RoomA, RoomB) VALUES (%s, %s)"
        cursor_local.execute(sql_insert_corridor, (row['RoomA'], row['RoomB']))
    print(f"Successfully migrated {len(corridor_records)} corridors.")

    # 3. INSERT ConfigJogo (Data from PHP)
    print("Inserting ConfigJogo data...")
    sql_config_query = """INSERT INTO ConfigJogo
                          (IDSimulacao, outliers_temperatura, outliers_som, alerta_temperatura_high,
                           alerta_temperatura_low, alerta_som, time_fecharcorredores, ruidolimite_fecharcorredores)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

    config_values = (
        php_vars["id_sim"], php_vars["out_temp"], php_vars["out_som"],
        php_vars["al_temp_h"], php_vars["al_temp_l"], php_vars["al_som"],
        php_vars["t_fechar"], php_vars["ruido_lim"]
    )

    cursor_local.execute(sql_config_query, config_values)
    print("ConfigJogo record inserted successfully.")

except Error as e:
    print(f"Database Error: {e}")
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor_local.close()
        connection.close()
    if 'connection_nuvem' in locals() and connection_nuvem.is_connected():
        cursor_nuvem.close()
        connection_nuvem.close()