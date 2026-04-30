import pymongo

class MongoDropper:
    def __init__(self):
        self.client = None
        self.portas = [27018, 27019, 27020]
        self.db_name = "pisid_maze"

    def connect_to_primary(self):
        """Localiza o nó Primary, pois só ele permite apagar a base de dados."""
        for porta in self.portas:
            try:
                temp_client = pymongo.MongoClient(
                    'localhost', 
                    porta, 
                    directConnection=True, 
                    serverSelectionTimeoutMS=2000
                )
                
                # O comando ismaster diz-nos se o nó é o líder (Primary)
                is_master_res = temp_client.admin.command('ismaster')
                
                if is_master_res.get('ismaster'):
                    print(f"✅ PRIMARY encontrado na porta {porta}.")
                    self.client = temp_client
                    return True
                else:
                    temp_client.close()
            except Exception as e:
                print(f"⚠️ Porta {porta} indisponível: {e}")
        
        print("❌ Erro: Não foi possível encontrar um nó PRIMARY no cluster.")
        return False

    def drop_everything(self):
        if not self.connect_to_primary():
            return

        try:
            print(f"🔍 Verificando coleções na base de dados '{self.db_name}'...")
            count = 0
            collections = self.client[self.db_name].list_collection_names()
            for collection in collections:
                docs = self.client[self.db_name][collection].find()
                for doc in docs:
                    isInserted = doc.get("inserted", False)

                    if not isInserted:
                        self.client[self.db_name][collection].update_one({"_id": doc["_id"]}, {"$set": {"inserted": True}})
                        count += 1
                        
            print(f"✅ Base de dados '{self.db_name}' limpa. Total de documentos marcados: {count}")

        except Exception as e:
            print(f"❌ Erro ao tentar fazer drop: {e}")
        finally:
            if self.client:
                self.client.close()

if __name__ == "__main__":
    dropper = MongoDropper()
    dropper.drop_everything()