import json
import pymongo
import paho.mqtt.client as mqtt

# Configurações globais
mqtt_broker = "broker.hivemq.com"
mqtt_port = 1883
topics = ["pisid_2_feedBack_temp", "pisid_2_feedBack_som", "pisid_2_feedBack_moves"]
database_name = "pisid_maze"

class FeedbackManager:
    def __init__(self):
        self.db = None
        self.clientMongoDB = None
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

    def connectToMongoDB(self):
        """Procura o nó PRIMARY nas portas 27018, 27019 e 27020."""
        mongo_nodes = [27018, 27019, 27020]
        
        print("🔎 À procura do nó PRIMARY no Cluster...")
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
                    self.db = self.clientMongoDB[database_name]
                    return True
                
                client_teste.close()
            except Exception:
                continue
        
        print("❌ ERRO: Não foi possível encontrar um nó PRIMARY ativo.")
        return False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ MQTT: Ligado ao Broker {mqtt_broker}")
            for topic in topics:
                client.subscribe(topic.strip())
                print(f"📡 Subscrito em: {topic.strip()}")
        else:
            print(f"MQTT: Erro código {rc} ao conectar ao Broker")

    def on_message(self, client, userdata, msg):
        try:
            raw_payload = msg.payload.decode().replace("'", '"')
            payload = json.loads(raw_payload)
            topico = msg.topic
            
            if "som" in topico:
                coll_name = 'sensor_ruido'
                outlier_coll_name = 'outliers_DadosErrados_ruido'
                tipo = "SOUND"
            elif "temp" in topico:
                coll_name = 'sensor_temperatura'
                outlier_coll_name = 'outliers_DadosErrados_temperatura'
                tipo = "TEMP"
            elif "mov" in topico:
                coll_name = 'sensor_movimento'
                outlier_coll_name = 'outliers_DadosErrados_movimento'
                tipo = "MOVIMENTO"
            else:
                return

            if payload.get('feedBack') is None:
                return

            success = False
            while not success:
                try:
                    colecao = self.db[coll_name]
                    id_inc = payload['idIncremental']

                    if payload['feedBack'] in [1, -2]:
                        colecao.update_one(
                            {"idIncremental": id_inc},
                            {"$set": {"inserted": True}}
                        )
                        print(f"✅ [{tipo}] ID {id_inc}: Marcado como inserido.")

                    elif payload['feedBack'] in [-1, -3, -4]:
                        doc = colecao.find_one({"idIncremental": id_inc})
                        if doc:
                            self.db[outlier_coll_name].insert_one(doc)
                            colecao.delete_one({"idIncremental": id_inc})
                            print(f"❌ [{tipo}] ID {id_inc}: Doc movido. {payload.get('feedBack')}")

                    elif payload['feedBack'] == 0:
                        print(f"⚠️ [{tipo}] ID {id_inc}: Feedback neutro, nada a fazer.")
                    

                    success = True # Sai do loop se tudo correu bem

                except (pymongo.errors.AutoReconnect, pymongo.errors.ServerSelectionTimeoutError, Exception) as e:
                    print(f"⚠️ Erro de DB: {e}. A tentar localizar novo PRIMARY...")
                    if not self.connectToMongoDB():
                        print("😴 Falha na reconexão. A aguardar 5s...")
                        import time
                        time.sleep(5)

        except Exception as e:
            print(f"Erro ao processar feedback: {e}")

    def run(self):
        if self.connectToMongoDB():
            try:
                print("A iniciar processamento de feedbacks...")
                self.mqtt_client.connect(mqtt_broker, mqtt_port, 60)
                self.mqtt_client.loop_forever()
            except KeyboardInterrupt:
                print("\n🛑 Script terminado pelo utilizador.")
            finally:
                if self.clientMongoDB:
                    self.clientMongoDB.close()
                    print("Conexão MongoDB fechada.")

if __name__ == "__main__":
    manager = FeedbackManager()
    manager.run()