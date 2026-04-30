import json
from django import db
import pymongo
import paho.mqtt.client as mqtt
from pymongo import MongoClient
#
#https://pypi.org/project/pymongo/
#https://www.emqx.com/en/blog/how-to-use-mqtt-in-python#real-world-python-mqtt-examples
#

class simToMongoDB:

    def __init__(self, topic, file_path=None):
        self.db = None # Variável global para a base de dados, para ser usada na função de callback do MQTT.
        self.clientMongoDB = None
        self.setMqtt(topic)
        self.file_path = file_path
        self.file = open(file_path, "w+") if file_path else None


    def setMqtt(self, topic):

        # Configurações MQTT
        self.mqtt_broker = "broker.hivemq.com"
        self.mqtt_port = 1883
        self.topic = topic
        
        # Inicializar o cliente MQTT dentro do objeto
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message


    def connectToMongoDB(self):
        # Mapeamento das portas que expuseste no Docker
        portas = [27018, 27019, 27020]
        timeout = 2000
        pisid = "pisid_maze"

        print("🔎 À procura do nó PRIMARY no Cluster...")

        for porta in portas:
            try:
                # Ligação direta a cada porta
                temp_client = pymongo.MongoClient(
                    'localhost', 
                    porta, 
                    directConnection=True, 
                    serverSelectionTimeoutMS=timeout
                )
                
                # Pergunta ao nó o seu estado
                is_master_res = temp_client.admin.command('ismaster')
                
                if is_master_res.get('ismaster'): # Se for True, é o Primary
                    print(f"✅ PRIMARY encontrado na porta {porta}!")
                    
                    # Guardamos este cliente e a base de dados na instância da classe
                    self.clientMongoDB = temp_client
                    self.db = self.clientMongoDB[pisid]
                    return # Sai da função assim que encontra o líder
                else:
                    print(f"ℹ️ Nó na porta {porta} é SECONDARY. A saltar...")
                    temp_client.close()

            except Exception as e:
                print(f"⚠️ Erro ao tentar porta {porta}: {e}")

        print("❌ Erro: Não foi possível encontrar um nó PRIMARY ativo.")


    def on_connect(self, client, userdata, flags, rc):

        if rc == 0:
            print(f"✅ MQTT: Ligado ao Broker {self.mqtt_broker}")
            try:
                # O .strip() remove qualquer lixo invisível (espaços, tabs, \r)
                filtro = self.topic.strip()
                client.subscribe(filtro)
                print(f"📡 Subscrito com sucesso em: {filtro}")
            except Exception as e:
                print(f"❌ Erro ao subscrever a {self.topic}: {e}")
        else:
            print(f"MQTT: Erro código {rc}")

    def on_message(self, client, userdata, msg):
        #Defini-se na classe filha, para assim processar os dados de forma diferente em função do tópico.
        pass

    def connect(self):
        try:
            print("A iniciar captura de dados...")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            print("\n🛑 Script terminado pelo utilizador.")
        finally:
            self.clientMongoDB.close()
            print("Conexão ao MongoDB fechada.")    

def main():
    sim_to_mongo = simToMongoDB("lol")
    sim_to_mongo.connectToMongoDB()
if __name__ == "__main__":
    main()
