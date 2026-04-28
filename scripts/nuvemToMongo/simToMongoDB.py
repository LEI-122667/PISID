import json
import pymongo
import paho.mqtt.client as mqtt

#
#https://pypi.org/project/pymongo/
#https://www.emqx.com/en/blog/how-to-use-mqtt-in-python#real-world-python-mqtt-examples
#

class simToMongoDB:

    def __init__(self, topic):
        self.db = None # Variável global para a base de dados, para ser usada na função de callback do MQTT.
        self.clientMongoDB = None
        self.setMqtt(topic)


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

        #URI com as credenciais root:root e porto 27017 (padrão do MongoDB).
        uri = "mongodb://root:root@localhost:27017/"
        timeout = 2000  # Tempo de espera - 2 segundos.
        pisid = "pisid_maze"

        #Try except caso mongoDB não esteja a correr ou as credenciais estejam erradas.
        try:
            #Estabelece a ligação, com um timeout.
            print("A tentar estabelecer ligação ao MongoDB...")
            self.clientMongoDB = pymongo.MongoClient(uri,serverSelectionTimeoutMS=timeout)
    
            # Testar se o servidor responde.
            self.clientMongoDB.server_info() 
            print("\nLigação ao MongoDB estabelecida com sucesso!\n")

            self.db = self.clientMongoDB[pisid]

        except Exception as e:
            print(f"Erro: {e}")


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