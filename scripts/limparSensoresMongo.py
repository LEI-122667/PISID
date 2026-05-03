import pymongo

uri = "mongodb://root:root@localhost:27018/"
timeout = 2000  # Tempo de espera - 2 segundos
collection_setup = "setup"
collection_corredores = "corredores"
db = None
collectionSetup= None
collectionCorredores = None
databaseMongo="pisid_maze"

mongo_nodes = [27018, 27019, 27020]
pisid_db_name = "pisid_maze"
primary_found = False
print("🔎 À procura do nó PRIMARY no Cluster...")
        
for porta in mongo_nodes:
    try:
                # Criamos um cliente temporário para testar a porta
                # directConnection=True é essencial para falar com um nó específico
                client_teste = pymongo.MongoClient(
                    'localhost', 
                    porta, 
                    directConnection=True, 
                    serverSelectionTimeoutMS=2000
                )
                
                # O comando ismaster diz-nos se este nó é o que aceita escritas (Primary)
                is_master_result = client_teste.admin.command('ismaster')
                
                if is_master_result.get('ismaster'):
                    print(f"✅ PRIMARY encontrado na porta {porta}!")
                    clientMongoDB = client_teste
                    db = clientMongoDB[pisid_db_name]
                    collectionSetup = db[collection_setup]
                    collectionCorredores = db[collection_corredores]
                    primary_found = True
                    break # Ligação estabelecida com sucesso
                else:                
                    client_teste.close()
                
    except Exception:
        continue
        
    print("❌ ERRO: Não foi possível encontrar um nó PRIMARY ativo.")

if primary_found:
    print("✅ Ligação estabelecida. A iniciar limpeza...")
    count = 0
    colecoes = ["sensor_movimento", "sensor_temperatura", "sensor_ruido"]
    
    for nome_colecao in colecoes:
        # ATENÇÃO: Verificamos 'inserted' (minúsculo) para coincidir com os outros scripts
        query = {'inserted': False}
        docs = db[nome_colecao].find(query)
        
        for doc in docs:
            db[nome_colecao].update_one(
                {'_id': doc['_id']}, 
                {'$set': {'inserted': True}}
            )
            count += 1
            
    print(f"🚀 Total de documentos atualizados: {count}")
else:
    print("❌ ERRO: Não foi possível encontrar um nó PRIMARY ativo. Operação cancelada.")
    