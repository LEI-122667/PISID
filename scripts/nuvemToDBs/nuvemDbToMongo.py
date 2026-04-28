import pymongo
import pymysql
from mysql.connector import Error
import mysql.connector as mariadb

userMongo="root"
passMongo="root"
hostMongo="localhost"
databaseMongo="pisid_maze"

nuvemuser="aluno"
nuvempass="aluno"
nuvemhost="194.210.86.10"
nuvemDb="maze"

uri = "mongodb://root:root@localhost:27017/"
timeout = 2000  # Tempo de espera - 2 segundos
collection_setup = "setup"
collection_corredores = "corredores"
db = None
collectionSetup= None
collectionCorredores = None

#Try except caso mongoDB não esteja a correr ou as credenciais estejam erradas.
try:

    #Estabelece a ligação, com um timeout.
    clientMongoDB = pymongo.MongoClient(uri, timeout)
    
    # Testar se o servidor responde.
    clientMongoDB.server_info() 
    print("\nLigação ao MongoDB estabelecida com sucesso!\n")

    db = clientMongoDB[databaseMongo]
    collectionSetup= db[collection_setup]
    collectionCorredores = db[collection_corredores]

except Exception as e:
        print(f"Erro: {e}")

'''
try:
    connection = mariadb.connect(host=hostmysql, user=usermysql,
    passwd=passmysql, db=database,connect_timeout=1000,autocommit=True)
    print("Connected to MySQL pisid_db")
except Error as e:
    print("Error while connecting to MySQL pisid_db", e)
'''

try:
    connection_nuvem = mariadb.connect(host=nuvemhost, user=nuvemuser,
    passwd=nuvempass, db=nuvemDb,connect_timeout=1000,autocommit=True)
    print("Connected to MySQL maze")
except Error as e:
    print("Error while connecting to MySQL maze", e)


sql_select_Query = "select * from SetupMaze"
cursor_nuvem = connection_nuvem.cursor(dictionary=True)
cursor_nuvem.execute(sql_select_Query)
records = cursor_nuvem.fetchall()

for row in records:
    for coluna, valor in row.items():
        print(f"{coluna} = {valor}")
    print("-" * 20) # Separador entre linhas


# This deletes the collection and all its documents
collectionSetup.drop()
print("Collection dropped successfully.")

#Insere os dados da tabela SetupMaze do MySQL maze para a coleção setup do MongoDB pisid_maze

for row in records:
    numbermarsamis = row['numbermarsamis']
    numberrooms = row['numberrooms']
    numberplayers = row['numberplayers']
    normalnoise = row['normalnoise']
    noisevartoleration = row['noisevartoleration']
    normaltemperature = row['normaltemperature']
    temperaturevarhightoleration = row['temperaturevarhightoleration']
    temperaturevarlowtoleration = row['temperaturevarlowtoleration']

    
    setup_doc = {
        "numbermarsamis": numbermarsamis,
        "numberrooms": numberrooms,
        "numberplayers": numberplayers,
        "normalnoise": float(row['normalnoise']),
        "noisevartoleration": float(row['noisevartoleration']),
        "normaltemperature": normaltemperature,
        "temperaturevarhightoleration": temperaturevarhightoleration,
        "temperaturevarlowtoleration": temperaturevarlowtoleration
    }

    collectionSetup.insert_one(setup_doc)
    print("Record inserted successfully into MongoDB setup collection")

sql_select_Query_corredores = "select * from Corridor"
cursor_nuvem2 = connection_nuvem.cursor(dictionary=True)
cursor_nuvem2.execute(sql_select_Query_corredores)
corredores = cursor_nuvem2.fetchall()

for row in corredores:
    for coluna, valor in row.items():
        print(f"{coluna} = {valor}")
    print("-" * 20) # Separador entre linhas

#Insere os dados da tabela Corredores do MySQL maze para a coleção corredores do MongoDB pisid_maze
collectionCorredores.drop()
print("Collection dropped successfully.")

i = 1
for row in corredores:
    corredor_doc = {
        "idCorredor": i,
        "origin": row['Rooma'],
        "destination": row['Roomb']
    }
    collectionCorredores.insert_one(corredor_doc)
    i += 1

print(f"Record inserted successfully into MongoDB {i-1} corredores collection")
    
















'''
ID = 1
numbermarsamis = 30
numberrooms = 10
numberplayers = 40
normalnoise = 10.00
noisevartoleration = 17.00
normaltemperature = 15
temperaturevarhightoleration = 10
temperaturevarlowtoleration = 10

for row in records:
    numbermarsamis = row['numbermarsamis']
    numberrooms = row['numberrooms']
    numberplayers = row['numberplayers']
    normalnoise = row['normalnoise']
    noisevartoleration = row['noisevartoleration']
    normaltemperature = row['normaltemperature']
    temperaturevarhightoleration = row['temperaturevarhightoleration']
    temperaturevarlowtoleration = row['temperaturevarlowtoleration']

    sql_insert_query = """INSERT INTO SetupMaze (NumberRooms, NumberMarsamis, NumberPlayers, NormalTemperature, TemperatureVarHighToleration, TemperatureVarLowToleration, NormalNoise, NoiseVarToleration) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    record_tuple = (numberrooms, numbermarsamis, numberplayers, normaltemperature, temperaturevarhightoleration, temperaturevarlowtoleration, normalnoise, noisevartoleration)
    
    cursor_mysql = connection.cursor()
    cursor_mysql.execute(sql_insert_query, record_tuple)
    connection.commit()
    print("Record inserted successfully into SetupMaze table")

'''