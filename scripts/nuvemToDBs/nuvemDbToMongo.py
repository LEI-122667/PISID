import pymongo
from mysql.connector import Error
import mysql.connector as mariadb

# --- Configuração MongoDB Replica Set ---
# Portas expostas no teu docker-compose para os 3 nós
MONGO_NODES = [27018, 27019, 27020]
databaseMongo = "pisid_maze"
collection_setup_name = "setup"
collection_corredores_name = "corredores"

# --- Configuração MariaDB Cloud ---
nuvemuser = "aluno"
nuvempass = "aluno"
nuvemhost = "194.210.86.10"
nuvemDb = "maze"

def get_mongo_primary():
    """Percorre os nós para encontrar qual deles é o Primary atual."""
    for porta in MONGO_NODES:
        try:
            client = pymongo.MongoClient(
                'localhost', 
                porta, 
                directConnection=True, 
                serverSelectionTimeoutMS=2000
            )
            # O comando ismaster identifica se o nó aceita escritas
            is_master = client.admin.command('ismaster')
            if is_master.get('ismaster'):
                print(f"✅ Ligado ao MongoDB Primary na porta {porta}")
                return client
            client.close()
        except Exception:
            continue
    return None

# --- Estabelecer Conexões ---

# 1. Conexão MongoDB
clientMongoDB = get_mongo_primary()

if clientMongoDB:
    db = clientMongoDB[databaseMongo]
    collectionSetup = db[collection_setup_name]
    collectionCorredores = db[collection_corredores_name]
else:
    print("❌ Erro: Não foi possível encontrar um nó Primary no MongoDB.")
    exit(1)

# 2. Conexão MariaDB Cloud
try:
    connection_nuvem = mariadb.connect(
        host=nuvemhost, 
        user=nuvemuser,
        passwd=nuvempass, 
        db=nuvemDb,
        connect_timeout=10, # Segundos
        autocommit=True
    )
    print("✅ Connected to MariaDB (Cloud)")
except Error as e:
    print(f"❌ Error connecting to MariaDB: {e}")
    exit(1)

# --- Processamento: SetupMaze ---
try:
    print("\nSincronizando SetupMaze...")
    cursor_nuvem = connection_nuvem.cursor(dictionary=True)
    cursor_nuvem.execute("SELECT * FROM SetupMaze")
    records = cursor_nuvem.fetchall()

    # Operação de escrita: Drop e Insert (Sempre no Primary)
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
    print(f"✅ {len(records)} registos inseridos na coleção 'setup'.")

    # --- Processamento: Corredores ---
    print("\nSincronizando Corredores...")
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
    print(f"✅ {i-1} corredores inseridos com sucesso.")

except Exception as e:
    print(f"❌ Erro durante a sincronização: {e}")

finally:
    # Fechar ligações
    if 'connection_nuvem' in locals():
        connection_nuvem.close()
    if 'clientMongoDB' in locals():
        clientMongoDB.close()
    print("\nConexões encerradas.")