import pymongo
import json
import pymongo
import paho.mqtt.client as mqtt

uri = "mongodb://root:root@localhost:27017/"
timeout = 2000  # Tempo de espera - 2 segundos
collection_setup = "setup"
collection_corredores = "corredores"
db = None
collectionSetup= None
collectionCorredores = None
databaseMongo="pisid_maze"
clientMongoDB = None
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

# Configurações MQTT
mqtt_broker = "broker.hivemq.com"
mqtt_port = 1883
topics = ["pisid_2_feedBack_temp", "pisid_2_feedBack_som", "pisid_2_feedBack_moves"]

def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ MQTT: Ligado ao Broker {mqtt_broker}")
            try:
                for topic in topics:
                    # O .strip() remove qualquer lixo invisível (espaços, tabs, \r)
                    filtro = topic.strip()
                    client.subscribe(filtro)
                    print(f"📡 Subscrito com sucesso em: {filtro}")
            except Exception as e:
                print(f"❌ Erro ao subscrever a {topic}: {e}")
        else:
            print(f"MQTT: Erro código {rc}")

def on_message(client, userdata, msg):
        try:
            # Converter a mensagem recebida para dicionário Python
            raw_payload = msg.payload.decode().replace("'", '"')
            payload = json.loads(raw_payload)
            print(f"\n📥 Mensagem recebida no tópico: {msg.topic}")


            topico = msg.topic

            if "som" in topico:
                colecao = db['sensor_ruido']
                tipo = "SOUND"
            elif "temp" in topico:
                colecao = db['sensor_temperatura']
                tipo = "TEMP"
            elif "mov" in topico:
                colecao = db['sensor_movimento']
                tipo = "MOVIMENTO"
            else:
                print(f"⚠️ Tópico desconhecido: {topico}")
                colecao = db['dados_desconecidos']
                tipo = "DESCONHECIDO"
                return
            
            if payload['feedBack'] is None:
                print(f"⚠️ Payload sem feedBack: {payload}")
                return
        
            if payload['feedBack'] == 1 or payload['feedBack'] == -2:
                 colecao.update_one(
                    {"idIncremental": payload['idIncremental']},
                    {"$set": {"inserted": True}}
                  )
                 print(f"✅ Feedback positivo recebido para idIncremental {payload['idIncremental']} - Documento marcado como inserido.")

            if payload['feedBack'] == 0:
                 print(f"⚠️ Feedback neutro recebido para idIncremental {payload['idIncremental']} - Nenhuma ação tomada.")
                 return

            if payload['feedBack'] == -1:
                 #Remover o documento da coleção, caso o feedback seja -1 (indica que o dado é inválido)
                 doc = colecao.find_one({"idIncremental": payload['idIncremental']})
                 if doc:
                    colecao.delete_one({"idIncremental": payload['idIncremental']})
                    if tipo == "SOUND":
                        db['outliers_DadosErrados_ruido'].insert_one(doc)
                    elif tipo == "TEMP":
                        db['outliers_DadosErrados_temperatura'].insert_one(doc)
                    elif tipo == "MOVIMENTO":
                        db['outliers_DadosErrados_movimento'].insert_one(doc)
                    print(f"❌ Feedback negativo recebido para idIncremental {payload['idIncremental']} - Documento removido e movido para coleção de outliers.")
                        
        except Exception as e:
            print(f"Erro ao processar mensagem no tópico {msg.topic}: {e}")

def connect():
    try:
        print("A iniciar captura de dados...")
        mqtt_client.connect(mqtt_broker, mqtt_port, 60)
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("\n🛑 Script terminado pelo utilizador.")
    finally:
        clientMongoDB.close()
        print("Conexão ao MongoDB fechada.")    

# Inicializar o cliente MQTT dentro do objeto
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

connect()