import json
from pydoc import doc
from time import sleep
import pymongo
import paho.mqtt.client as mqtt
from datetime import datetime, timezone, timedelta
from collections import deque

class mongoToMqtt:
    def __init__(self, topic, collection_name, outlier_collection_name):
        self.db = None
        self.clientMongoDB = None
        self.collection = None
        self.collection_name = collection_name
        self.outlier_collection_name = outlier_collection_name
        self.setMqtt(topic)
        if self.collection_name != 'sensor_movimento':
            self.janela = deque(maxlen=5)

    def getJanelaAverage(self):
        if not self.janela:
            return None
        return sum(self.janela) / len(self.janela)

    def setMqtt(self, topic):
    
        # Configurações MQTT
        self.mqtt_broker = "broker.hivemq.com"
        self.mqtt_port = 1883
        self.topic = topic
        
        # Inicializar o cliente MQTT dentro do objeto
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_publish = self.on_publish_callback
        self.motivo_outlier = ""

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ MQTT: Ligado ao Broker {self.mqtt_broker}")
        else:
            print(f"MQTT: Erro código {rc}")

    def on_publish_callback(self, client, userdata, mid):
        # Esta função é chamada internamente pela biblioteca após cada envio
        pass

    def connectToMongoDB(self):
        mongo_nodes = [27018, 27019, 27020]
        pisid_db_name = "pisid_maze"
        
        print("🔎 À procura do nó PRIMARY no Cluster (sem autenticação)...")
        
        for porta in mongo_nodes:
            try:
                uri = f"mongodb://localhost:{porta}/"
                
                client_teste = pymongo.MongoClient(
                    uri, 
                    directConnection=True, 
                    serverSelectionTimeoutMS=2000
                )
                
                is_master_result = client_teste.admin.command('ismaster')
                
                if is_master_result.get('ismaster'):
                    print(f"✅ PRIMARY encontrado na porta {porta}!")
                    self.clientMongoDB = client_teste
                    self.db = self.clientMongoDB[pisid_db_name]
                    
                    self.collection = self.db[self.collection_name]
                    self.outlier_collection = self.db[self.outlier_collection_name]
                    return True 
                
                client_teste.close()
                
            except Exception:
                continue
        
        print("❌ ERRO: Não foi possível encontrar um nó PRIMARY ativo.")
        return False

    def publishData(self, client):
        while True:
            try:
                query = {"inserted": False, "timeSent": None}
                unread_documents = self.collection.find(query).sort("idIncremental", 1)
                
                for doc in unread_documents:
                    if self.isOutlier(doc):
                        self.handleOutlier(doc)
                    else:
                        self.sendDoc(doc, client, label="Enviado")


                retry_limit = datetime.now(timezone.utc) - timedelta(seconds=3)
                retry_query = {"inserted": False, "timeSent": {"$ne": None, "$lte": retry_limit}}
                
                documents_to_resend = self.collection.find(retry_query)
                
                for doc in documents_to_resend:
                    self.sendDoc(doc, client, label="Reenviado")
                            
                sleep(5)

            except (pymongo.errors.AutoReconnect, pymongo.errors.ServerSelectionTimeoutError, Exception) as e:
                print(f"⚠️ Conexão perdida no loop de publicação: {e}")
                print("🔎 A tentar localizar novo PRIMARY...")
                
                if self.connectToMongoDB():
                    print("✅ Reconexão bem-sucedida. A retomar processamento...")
                else:
                    print("😴 Falha na reconexão. A aguardar 5s para nova tentativa...")
                    sleep(5)

    def sendDoc(self, doc, client, label="Enviado"):
        try:
            payload_doc = doc.copy()
            payload_doc["_id"] = None
            
            time_now = datetime.now(timezone.utc)
            payload_doc["timeSent"] = time_now
            
            payload = json.dumps(payload_doc, default=str)   
            client.publish(self.topic, payload, qos=1)
            
            self.collection.update_one(
                {"_id": doc["_id"]}, 
                {"$set": {"timeSent": time_now}}
            )
            
            icon = "📤" if label == "Enviado" else "🔄"
            print(f"{icon} Documento {label}: ID: {doc.get('idIncremental')}")
        except Exception as e:
            raise e

    def isOutlier(self, doc):
        pass # Depende do topico

    def handleOutlier(self, doc):
        doc['motivo_outlier'] = self.motivo_outlier
        doc['data_filtro'] = datetime.now(timezone.utc)
        self.outlier_collection.insert_one(doc)
        self.collection.delete_one({"_id": doc["_id"]})
    
    def sendingLoop(self):  
        if self.db is None:
            print("⚠️ Erro: Conexão não estabelecida. Script terminado.")
            return

        try:
            print("A iniciar envio de dados...")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            self.publishData(self.mqtt_client)
            self.mqtt_client.loop_stop()
        except KeyboardInterrupt:
            print("\n🛑 Script terminado pelo utilizador.")
        finally:
            self.clientMongoDB.close()
