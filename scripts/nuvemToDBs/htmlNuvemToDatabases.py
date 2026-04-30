import mysql.connector as mariadb
from mysql.connector import Error
import pymongo
import sys

# --- Configuration: MariaDB Local ---
usermysql, passmysql, hostmysql, database = "root", "root", "localhost", "bd_pisid"

# --- Configuration: MariaDB Cloud ---
nuvemuser, nuvempass, nuvemhost, nuvemDb = "aluno", "aluno", "194.210.86.10", "maze"

# --- Configuration: MongoDB ---
uri = "mongodb://root:root@localhost:27017/"
databaseMongo = "pisid_maze"
collection_setup_name = "setup"
collection_corredores_name = "corredores"

# --- 1. Capture Arguments from PHP ---
# Expected order: [IDSimulacao, outliers_temp, outliers_som, alerta_temp_h, alerta_temp_l, alerta_som, time_fechar, ruido_limite, amount_of_gatilhos]
id_sim = sys.argv[1] if len(sys.argv) > 1 else "1"
php_vars = {
    "id_sim": id_sim,
    "out_temp": sys.argv[2] if len(sys.argv) > 2 else "2.0",
    "out_som": sys.argv[3] if len(sys.argv) > 3 else "2.0",
    "al_temp_h": sys.argv[4] if len(sys.argv) > 4 else "5",
    "al_temp_l": sys.argv[5] if len(sys.argv) > 5 else "5",
    "al_som": sys.argv[6] if len(sys.argv) > 6 else "5",
    "t_fechar": sys.argv[7] if len(sys.argv) > 7 else "10",
    "ruido_lim": sys.argv[8] if len(sys.argv) > 8 else "0",
    "amt_gatilhos": sys.argv[9] if len(sys.argv) > 9 else "3"
}

try:
    # --- 2. Establish Connections ---

    # MariaDB Local
    conn_local = mariadb.connect(host=hostmysql, user=usermysql, passwd=passmysql, db=database, autocommit=True)
    cursor_local = conn_local.cursor()
    print("Connected to Local MariaDB.")

    # MariaDB Cloud
    conn_nuvem = mariadb.connect(host=nuvemhost, user=nuvemuser, passwd=nuvempass, db=nuvemDb, autocommit=True)
    cursor_nuvem = conn_nuvem.cursor(dictionary=True)
    print("Connected to Cloud MariaDB.")

    # MongoDB
    client_mongo = pymongo.MongoClient(uri, serverSelectionTimeoutMS=2000)
    client_mongo.server_info()  # Test connection
    db_mongo = client_mongo[databaseMongo]
    col_setup = db_mongo[collection_setup_name]
    col_corredores = db_mongo[collection_corredores_name]
    print("Connected to MongoDB.")

    # --- 3. Process SetupMaze ---
    print("\nSyncing SetupMaze...")
    cursor_nuvem.execute("SELECT * FROM SetupMaze")
    records = cursor_nuvem.fetchall()

    # Reset MongoDB collection
    col_setup.drop()

    for row in records:
        # A. Insert into Local MariaDB
        sql_mariadb = """INSERT INTO SetupMaze (IDSimulacao, NumberRooms, NumberMarsamis, NumberPlayers, NormalTemperature,
                                                TemperatureVarHighToleration, TemperatureVarLowToleration, NormalNoise, \
                                                NoiseVarToleration)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        cursor_local.execute(sql_mariadb, (
            php_vars['id_sim'], row['numberrooms'], row['numbermarsamis'], row['numberplayers'],
            row['normaltemperature'], row['temperaturevarhightoleration'],
            row['temperaturevarlowtoleration'], row['normalnoise'], row['noisevartoleration']
        ))

        # B. Insert into MongoDB (Adding the extra PHP arguments)
        setup_doc = {
            "numbermarsamis": row['numbermarsamis'],
            "numberrooms": row['numberrooms'],
            "numberplayers": row['numberplayers'],
            "normalnoise": float(row['normalnoise']),
            "noisevartoleration": float(row['noisevartoleration']),
            "normaltemperature": row['normaltemperature'],
            "temperaturevarhightoleration": row['temperaturevarhightoleration'],
            "temperaturevarlowtoleration": row['temperaturevarlowtoleration'],
            # Adding the arguments from PHP
            "outliers_temperatura": float(php_vars["out_temp"]),
            "outliers_som": float(php_vars["out_som"]),
            "IDSimulacao": int(php_vars["id_sim"])
        }
        col_setup.insert_one(setup_doc)

    # --- 4. Process Corridors ---
    print("Syncing Corridors...")
    cursor_nuvem.execute("SELECT Rooma, Roomb FROM Corridor")
    corredores = cursor_nuvem.fetchall()

    col_corredores.drop()

    for i, row in enumerate(corredores, start=1):
        # A. MariaDB Local
        cursor_local.execute("INSERT INTO Corridor (IDSimulacao, RoomA, RoomB) VALUES (%s, %s, %s)", (php_vars['id_sim'], row['Rooma'], row['Roomb']))

        # B. MongoDB
        corredor_doc = {
            "idCorredor": i,
            "origin": row['Rooma'],
            "destination": row['Roomb']
        }
        col_corredores.insert_one(corredor_doc)

    # --- 5. Insert ConfigJogo (MariaDB Only) ---
    print("Inserting ConfigJogo...")
    sql_config = """INSERT INTO ConfigJogo
                    (IDSimulacao, outliers_temperatura, outliers_som, alerta_temperatura_high,
                     alerta_temperatura_low, alerta_som, time_fecharcorredores, ruidolimite_fecharcorredores, amount_of_gatilhos)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    config_vals = (
        php_vars["id_sim"], php_vars["out_temp"], php_vars["out_som"],
        php_vars["al_temp_h"], php_vars["al_temp_l"], php_vars["al_som"],
        php_vars["t_fechar"], php_vars["ruido_lim"], php_vars["amt_gatilhos"]
    )
    cursor_local.execute(sql_config, config_vals)

    print("\nAll systems synchronized successfully.")

except Exception as e:
    print(f"\nFATAL ERROR: {e}")

finally:
    if 'conn_local' in locals(): conn_local.close()
    if 'conn_nuvem' in locals(): conn_nuvem.close()
    if 'client_mongo' in locals(): client_mongo.close()