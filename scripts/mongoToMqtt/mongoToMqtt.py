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
        if not self.collection == 'sensor_movimento':
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
        self.mqtt_client = mqtt.Client(transport="tcp")
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
        #URI com as credenciais root
        uri = "mongodb://root:root@localhost:27017/"
        timeout = 2000  # Tempo de espera - 2 segundos
        pisid = "pisid_maze"

        #Try except caso mongoDB não esteja a correr ou as credenciais estejam erradas.
        try:

            #Estabelece a ligação, com um timeout.
            self.clientMongoDB = pymongo.MongoClient(uri, timeout)
    
            # Testar se o servidor responde.
            self.clientMongoDB.server_info() 
            print("\nLigação ao MongoDB estabelecida com sucesso!\n")

            self.db = self.clientMongoDB[pisid]
            self.collection = self.db[self.collection_name]
            self.outlier_collection = self.db[self.outlier_collection_name]

        except Exception as e:
             print(f"Erro: {e}")

    def publishData(self,  client):
        while True:
            try:
                
                # Busca documentos não processados ordenados por tempo (ObjectId)
                query = {"inserted": False, "timeSent": None}
                
                # FIX 3: Sort 1 (Ascending) so the cursor walks toward new data
                unread_documents = self.collection.find(query).sort("idIncremental", 1)
                
                for doc in unread_documents:
                    if (self.isOutlier(doc)):
                        self.handleOutlier(doc)
                    else:
                        self.sendDoc(doc, client)

                retry_limit = datetime.now(timezone.utc) - timedelta(seconds=3)
                retry_query = {"inserted": False, "timeSent": {"$lte": retry_limit}}
                
                documents_to_resend = self.collection.find(retry_query)
                
                for doc in documents_to_resend:
                    self.resend(doc)
                            
                sleep(1)
            except Exception as e:
                print(f"Erro ao publicar ruído: {e}")
                sleep(1)

    def resend(self, doc):
        try:
            payload_doc = doc.copy()
            payload_doc["_id"] = None
            time = datetime.now(timezone.utc)
            payload_doc["timeSent"] = time 
            payload = json.dumps(payload_doc, default=str)
            self.mqtt_client.publish(self.topic, payload, qos=1)
            self.collection.update_one( {"_id": doc["_id"]}, {"$set": {"timeSent": time}})
            print(f"🔄 Documento reenviado no tópico {self.topic}: ID: {doc.get('idIncremental')}")
        
        except Exception as e:
            print(f"Erro ao reenviar movimento: {e}")

    def isOutlier(self, doc):
        pass # Depende do topico

    def handleOutlier(self, doc):
        doc['motivo_outlier'] = self.motivo_outlier
        doc['data_filtro'] = datetime.now(timezone.utc)
        self.outlier_collection.insert_one(doc)
        self.collection.delete_one({"_id": doc["_id"]})
    
    def sendDoc(self, doc, client):
        payload_doc = doc.copy()
        payload_doc["_id"] = None
        time = datetime.now(timezone.utc)
        payload_doc["timeSent"] = time
        payload = json.dumps(payload_doc, default=str)   
        client.publish(self.topic, payload, qos=1)
        self.collection.update_one( {"_id": doc["_id"]}, {"$set": {"timeSent": time}})
        print(f"📤 Documento enviado no tópico {self.topic}: ID: {doc.get('idIncremental')}")

    def sendingLoop(self):  
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
