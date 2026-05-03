import json
import pymongo
import mysql.connector as mariadb
from mysql.connector import Error

# --- CONFIGURAÇÕES ---
databaseMongo = "pisid_maze"
collection_setup = "setup"
collection_corredores = "corredores"

nuvemuser = "aluno"
nuvempass = "aluno"
nuvemhost = "194.210.86.10"
nuvemDb = "maze"

# Variáveis globais para o MongoDB
clientMongoDB = None
db = None
collectionSetup = None
collectionCorredores = None

def connectToMongoDB():

    global clientMongoDB, db, collectionSetup, collectionCorredores
    mongo_nodes = [27018, 27019, 27020]
    
    print("🔎 À procura do nó PRIMARY no Cluster MongoDB...")
    for porta in mongo_nodes:
        try:
            uri = f"mongodb://localhost:{porta}/"
            teste_client = pymongo.MongoClient(uri, directConnection=True, serverSelectionTimeoutMS=2000)
            
            is_master = teste_client.admin.command('ismaster')
            
            if is_master.get('ismaster'):
                print(f"✅ PRIMARY encontrado na porta {porta}!")
                clientMongoDB = teste_client
                db = clientMongoDB[databaseMongo]
                collectionSetup = db[collection_setup]
                collectionCorredores = db[collection_corredores]
                return True
            
            teste_client.close()
        except Exception:
            continue
    
    print("❌ ERRO: Não foi possível encontrar um nó PRIMARY ativo.")
    return False

# --- INÍCIO DO PROCESSO ---

if not connectToMongoDB():
    exit(1)

try:
    connection_nuvem = mariadb.connect(
        host=nuvemhost, user=nuvemuser, passwd=nuvempass, 
        db=nuvemDb, connect_timeout=1000, autocommit=True
    )
    print("✅ Connected to MySQL maze (Nuvem)")
except Error as e:
    print(f"❌ Error while connecting to MySQL maze: {e}")
    exit(1)

cursor_nuvem = connection_nuvem.cursor(dictionary=True)

# --- MIGRAÇÃO: SETUP ---
print("\n--- Migrando SetupMaze ---")
try:
    cursor_nuvem.execute("SELECT * FROM SetupMaze")
    records = cursor_nuvem.fetchall()

    collectionSetup.drop()
    print("Collection 'setup' limpa.")

    for row in records:
        setup_doc = {
            "numbermarsamis": row['numbermarsamis'],
            "numberrooms": row['numberrooms'],
            "numberplayers": row['numberplayers'],
            "normalnoise": float(row['normalnoise']),
            "noisevartoleration": float(row['noisevartoleration']),
            "normaltemperature": row['normaltemperature'],
            "temperaturevarhightoleration": row['temperaturevarhightoleration'],
            "temperaturevarlowtoleration": row['temperaturevarlowtoleration']
        }
        collectionSetup.insert_one(setup_doc)
    print(f"✅ {len(records)} registros de Setup inseridos.")

except Exception as e:
    print(f"❌ Erro na migração de Setup: {e}")

# --- MIGRAÇÃO: CORREDORES ---
print("\n--- Migrando Corredores ---")
try:
    cursor_nuvem.execute("SELECT * FROM Corridor")
    corredores = cursor_nuvem.fetchall()

    collectionCorredores.drop()
    print("Collection 'corredores' limpa.")

    i = 1
    for row in corredores:
        corredor_doc = {
            "idCorredor": i,
            "origin": row['Rooma'],
            "destination": row['Roomb']
        }
        collectionCorredores.insert_one(corredor_doc)
        i += 1
    print(f"✅ {i-1} corredores inseridos.")

except Exception as e:
    print(f"❌ Erro na migração de Corredores: {e}")



connection_nuvem.close()
clientMongoDB.close()
print("\n🏁 Processo terminado com sucesso.")