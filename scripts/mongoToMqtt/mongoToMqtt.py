from datetime import datetime, timezone, timedelta
import json
from time import sleep
import pymongo
import paho.mqtt.client as mqtt
from collections import deque

class mongoToMqtt:
    def __init__(self, topic, collection_name, outlier_collection_name):
        self.db = None
        self.clientMongoDB = None
        self.collection = None
        self.collection_name = collection_name
        self.outlier_collection_name = outlier_collection_name
        self.mongo_nodes = [27018, 27019, 27020] # Portas locais para réplicas
        self.setMqtt(topic)
        if not self.collection_name == 'sensor_movimento':
            self.janela = deque(maxlen=5)

    def getJanelaAverage(self):
        if not self.janela:
            return None
        return sum(self.janela) / len(self.janela)

    def setMqtt(self, topic):
        self.mqtt_broker = "broker.hivemq.com"
        self.mqtt_port = 1883
        self.topic = topic
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
        pass

    def connectToMongoDB(self):
        """Descobre o Primary no Replica Set sem usar autenticação e de forma portátil."""
        for porta in self.mongo_nodes:
            try:
                client = pymongo.MongoClient(
                    'localhost', 
                    porta, 
                    directConnection=True, 
                    serverSelectionTimeoutMS=2000
                )
                if client.admin.command('ismaster').get('ismaster'):
                    print(f"✅ MongoDB Primary encontrado na porta {porta} para coleção {self.collection_name}")
                    self.clientMongoDB = client
                    self.db = self.clientMongoDB["pisid_maze"]
                    self.collection = self.db[self.collection_name]
                    self.outlier_collection = self.db[self.outlier_collection_name]
                    return True
                client.close()
            except Exception:
                continue
        print("❌ Erro: Não foi possível encontrar o nó Primary.")
        return False

    def publishData(self, client):
        while True:
            try:
                # 1. Busca documentos não processados
                query = {"inserted": False, "timeSent": None}
                unread_documents = self.collection.find(query).sort("idIncremental", 1)
                
                for doc in unread_documents:
                    if self.isOutlier(doc):
                        self.handleOutlier(doc)
                    else:
                        self.sendDoc(doc, client)

                # 2. Lógica de Reenvio (para documentos sem feedback após 3 segundos)
                retry_limit = datetime.now(timezone.utc) - timedelta(seconds=3)
                retry_query = {"inserted": False, "timeSent": {"$lte": retry_limit}}
                
                documents_to_resend = self.collection.find(retry_query)
                for doc in documents_to_resend:
                    self.resend(doc)
                            
                sleep(1)
            except (pymongo.errors.AutoReconnect, pymongo.errors.PyMongoError) as e:
        # Verificamos se o erro é sobre não ser primary ou perda de ligação
                if "not primary" in str(e).lower() or "reconnect" in str(e).lower():
                    print("⚠️ Conexão perdida ou Nó não é Primary. Reconectando...")
                    self.connectToMongoDB()
                    sleep(1)
            except Exception as e:
                print(f"Erro no loop de publicação: {e}")
                sleep(1)

    def resend(self, doc):
        try:
            payload_doc = doc.copy()
            payload_doc["_id"] = None
            utc_plus_one = timezone(timedelta(hours=1))
            time_now = datetime.now(utc_plus_one)
            payload_doc["timeSent"] = time_now
            payload = json.dumps(payload_doc, default=str)
            
            self.mqtt_client.publish(self.topic, payload, qos=1)
            self.collection.update_one({"_id": doc["_id"]}, {"$set": {"timeSent": time_now}})
            print(f"🔄 Reenviado: ID {doc.get('idIncremental')} no tópico {self.topic}, HoraEnviada: {payload_doc['timeSent']}, Hora: {payload_doc['Hour']}")
        
        except (pymongo.errors.AutoReconnect, pymongo.errors.PyMongoError) as e:
        # Verificamos se o erro é sobre não ser primary ou perda de ligação
            if "not primary" in str(e).lower() or "reconnect" in str(e).lower():
                print("⚠️ Conexão perdida ou Nó não é Primary. Reconectando...")
                self.connectToMongoDB()
                sleep(1)
        except Exception as e:
            print(f"Erro ao reenviar: {e}")

    def isOutlier(self, doc):
        return False # Override nas classes filhas

    def handleOutlier(self, doc):
        try:
            doc['motivo_outlier'] = self.motivo_outlier
            doc['data_filtro'] = datetime.now(timezone.utc)
            self.outlier_collection.insert_one(doc)
            self.collection.delete_one({"_id": doc["_id"]})
            print(f"🗑️ Outlier movido: ID {doc.get('idIncremental')}")
        except Exception as e:
            print(f"Erro ao tratar outlier: {e}")
    
    def sendDoc(self, doc, client):
        try:
            payload_doc = doc.copy()
            payload_doc["_id"] = None            
            utc_plus_one = timezone(timedelta(hours=1))
            time_now = datetime.now(utc_plus_one)
            payload_doc["timeSent"] = time_now
            payload = json.dumps(payload_doc, default=str)   
            
            client.publish(self.topic, payload, qos=1)
            self.collection.update_one({"_id": doc["_id"]}, {"$set": {"timeSent": time_now}})
            print(f"📤 Enviado: ID {doc.get('idIncremental')} no tópico {self.topic} HoraEnviada: {payload_doc['timeSent']}, Hora: {payload_doc['Hour']}")
        except Exception as e:
            print(f"Erro ao enviar documento: {e}")

    def sendingLoop(self):  
        try:
            if not self.clientMongoDB:
                self.connectToMongoDB()
            
            print(f"🚀 A iniciar worker para {self.topic}...")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            self.publishData(self.mqtt_client)
        except KeyboardInterrupt:
            print("\n🛑 Script terminado pelo utilizador.")
        finally:
            if self.clientMongoDB:
                self.clientMongoDB.close()
            self.mqtt_client.loop_stop()