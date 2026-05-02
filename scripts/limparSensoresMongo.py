import pymongo

uri = "mongodb://root:root@localhost:27018/"
timeout = 2000  # Tempo de espera - 2 segundos
collection_setup = "setup"
collection_corredores = "corredores"
db = None
collectionSetup= None
collectionCorredores = None
databaseMongo="pisid_maze"

#Try except caso mongoDB não esteja a correr ou as credenciais estejam erradas.
try:

    #Estabelece a ligação, com um timeout.
    clientMongoDB = pymongo.MongoClient(uri, timeout)
    
    # Testar se o servidor responde.
    clientMongoDB.server_info() 
    print("\nLigação ao MongoDB estabelecida com sucesso!\n")

    db = clientMongoDB[databaseMongo]

except Exception as e:
        print(f"Erro: {e}")

count = 0
colecoes = ["sensor_movimento", "sensor_temperatura", "sensor_ruido"]
for colecao in colecoes:
    docs = db[colecao].find({'Inserted': False})
    for doc in docs:
        db[colecao].update_one({'_id': doc['_id']}, {'$set': {'Inserted': True}})
        count += 1
        
print(f"Total de documentos atualizados: {count}")
    