import json
import os
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
        """
        Tenta encontrar o nó PRIMARY dentro do cluster local (Replica Set).
        As portas padrão configuradas são 27018, 27019 e 27020.
        """
        mongo_nodes = [27018, 27019, 27020]
        pisid_db_name = "pisid_maze"
        
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
                    self.clientMongoDB = client_teste
                    self.db = self.clientMongoDB[pisid_db_name]
                    return True # Ligação estabelecida com sucesso
                
                client_teste.close()
                
            except Exception:
                # Se falhar nesta porta, apenas ignoramos e tentamos a próxima
                continue
        
        print("❌ ERRO: Não foi possível encontrar um nó PRIMARY ativo.")
        return False

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
            print(f"MQTT: Erro código {rc} ao conectar ao broker")

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

    def getId(self, topic):
        if topic == "sensor_movimento":
            fileName = "last_id_sensor_movimento.txt"
            colecao = self.db["sensor_movimento"]
        elif topic == "sensor_temperatura":
            fileName = "last_id_sensor_temperatura.txt"
            colecao = self.db["sensor_temperatura"]
        else:
            fileName = "last_id_sensor_ruido.txt"
            colecao = self.db["sensor_ruido"]
        
        file_path = os.path.join(os.path.dirname(__file__), "..", fileName)

        last_id = None
         
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read().strip()
                if content:
                    last_id = int(content)

        if last_id is None:
            ultimo_registro = list(colecao.find().sort("idIncremental", -1).limit(1))
            if ultimo_registro:
                last_id = int(ultimo_registro[0].get('idIncremental', 0))
            else:
                last_id = 0

        new_id = last_id + 1
        with open(file_path, "w") as f: 
            f.write(str(new_id))
        
        return new_id