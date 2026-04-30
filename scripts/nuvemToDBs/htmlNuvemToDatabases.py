import mysql.connector as mariadb
from mysql.connector import Error
import pymongo
import sys

# --- Configuration: MariaDB Local ---
usermysql, passmysql, hostmysql, database = "root", "root", "localhost", "bd_pisid"

# --- Configuration: MariaDB Cloud ---
nuvemuser, nuvempass, nuvemhost, nuvemDb = "aluno", "aluno", "194.210.86.10", "maze"

# --- Configuration: MongoDB Replica Set ---
# Portas mapeadas no docker-compose
MONGO_NODES = [27018, 27019, 27020]
databaseMongo = "pisid_maze"
collection_setup_name = "setup"
collection_corredores_name = "corredores"

def get_mongo_primary():
    """Tenta encontrar o nó Primary no cluster de réplicas."""
    for porta in MONGO_NODES:
        try:
            client = pymongo.MongoClient(
                'localhost', 
                porta, 
                directConnection=True, 
                serverSelectionTimeoutMS=2000
            )
            is_master = client.admin.command('ismaster')
            if is_master.get('ismaster'):
                print(f"✅ MongoDB Primary encontrado na porta {porta}.")
                return client
            client.close()
        except Exception as e:
            print(f"⚠️ Porta {porta} indisponível ou secundária.")
    return None

# --- 1. Capture Arguments from PHP ---
try:
    php_vars = {
        "id_sim": sys.argv[1],
        "out_temp": sys.argv[2],
        "out_som": sys.argv[3],
        "al_temp_h": sys.argv[4],
        "al_temp_l": sys.argv[5],
        "al_som": sys.argv[6],
        "t_fechar": sys.argv[7],
        "ruido_lim": sys.argv[8],
        "amt_gatilhos": sys.argv[9]
    }
except IndexError:
    print("Error: Missing arguments from PHP. Script requires 9 arguments.")
    sys.exit(1)

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

    # MongoDB (Procura o Primary para permitir DROP e INSERT)
    client_mongo = get_mongo_primary()
    if not client_mongo:
        raise Exception("Não foi possível encontrar um nó Primary no MongoDB Replica Set.")
    
    db_mongo = client_mongo[databaseMongo]
    col_setup = db_mongo[collection_setup_name]
    col_corredores = db_mongo[collection_corredores_name]

    # --- 3. Process SetupMaze ---
    print("\nSyncing SetupMaze...")
    cursor_nuvem.execute("SELECT * FROM SetupMaze")
    records = cursor_nuvem.fetchall()

    # Reset MongoDB collection (Operação de escrita, requer Primary)
    col_setup.drop()

    for row in records:
        # A. Insert into Local MariaDB
        sql_mariadb = """INSERT INTO SetupMaze (NumberRooms, NumberMarsamis, NumberPlayers, NormalTemperature,
                                                TemperatureVarHighToleration, TemperatureVarLowToleration, NormalNoise, \
                                                NoiseVarToleration)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

        cursor_local.execute(sql_mariadb, (
            row['numberrooms'], row['numbermarsamis'], row['numberplayers'],
            row['normaltemperature'], row['temperaturevarhightoleration'],
            row['temperaturevarlowtoleration'], row['normalnoise'], row['noisevartoleration']
        ))

        # B. Insert into MongoDB
        setup_doc = {
            "numbermarsamis": row['numbermarsamis'],
            "numberrooms": row['numberrooms'],
            "numberplayers": row['numberplayers'],
            "normalnoise": float(row['normalnoise']),
            "noisevartoleration": float(row['noisevartoleration']),
            "normaltemperature": row['normaltemperature'],
            "temperaturevarhightoleration": row['temperaturevarhightoleration'],
            "temperaturevarlowtoleration": row['temperaturevarlowtoleration'],
            "outliers_temperatura": float(php_vars["out_temp"]),
            "outliers_som": float(php_vars["out_som"]),
            "IDSimulacao": int(php_vars["id_sim"])
        }
        col_setup.insert_one(setup_doc)

    # --- 4. Process Corridors ---
    print("Syncing Corridors...")
    cursor_nuvem.execute("SELECT Rooma, Roomb FROM Corridor")
    corredores = cursor_nuvem.fetchall()

    col_corredores.drop() # Requer Primary

    for i, row in enumerate(corredores, start=1):
        # A. MariaDB Local
        cursor_local.execute("INSERT INTO Corridor (RoomA, RoomB) VALUES (%s, %s)", (row['Rooma'], row['Roomb']))

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
    if 'client_mongo' in locals() and client_mongo: client_mongo.close()