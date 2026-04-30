import pymongo
import json
import paho.mqtt.client as mqtt
import time

# --- Configuração MongoDB Replica Set ---
MONGO_NODES = [27018, 27019, 27020]
databaseMongo = "pisid_maze"
clientMongoDB = None
db = None

def get_mongo_primary():
    """Tenta localizar o nó Primary no Replica Set."""
    for porta in MONGO_NODES:
        try:
            client = pymongo.MongoClient(
                'localhost', 
                porta, 
                directConnection=True, 
                serverSelectionTimeoutMS=2000
            )
            if client.admin.command('ismaster').get('ismaster'):
                print(f"✅ MongoDB Primary encontrado na porta {porta}.")
                return client
            client.close()
        except Exception:
            continue
    return None

def connect_to_mongo():
    """Inicializa ou atualiza a conexão com o Primary."""
    global clientMongoDB, db
    new_client = get_mongo_primary()
    if new_client:
        clientMongoDB = new_client
        db = clientMongoDB[databaseMongo]
        return True
    return False

# Inicializar conexão antes de começar o MQTT
if not connect_to_mongo():
    print("❌ Erro Fatal: Não foi possível ligar ao MongoDB Primary.")
    exit(1)

# --- Configurações MQTT ---
mqtt_broker = "broker.hivemq.com"
mqtt_port = 1883
topics = ["pisid_2_feedBack_temp", "pisid_2_feedBack_som", "pisid_2_feedBack_moves"]

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ MQTT: Ligado ao Broker {mqtt_broker}")
        for topic in topics:
            client.subscribe(topic.strip())
            print(f"📡 Subscrito em: {topic}")
    else:
        print(f"MQTT: Erro código {rc}")

def on_message(client, userdata, msg):
    global db
    try:
        raw_payload = msg.payload.decode().replace("'", '"')
        payload = json.loads(raw_payload)
        topico = msg.topic
        
        # Identificar coleções baseadas no tópico
        if "som" in topico:
            colecao_nome = 'sensor_ruido'
            outlier_nome = 'outliers_DadosErrados_ruido'
        elif "temp" in topico:
            colecao_nome = 'sensor_temperatura'
            outlier_nome = 'outliers_DadosErrados_temperatura'
        elif "mov" in topico:
            colecao_nome = 'sensor_movimento'
            outlier_nome = 'outliers_DadosErrados_movimento'
        else:
            return

        if payload.get('feedBack') is None:
            return

        id_inc = payload['idIncremental']

        # Tentar realizar a operação no Mongo
        try:
            colecao = db[colecao_nome]

            # Caso 1: Sucesso ou Duplicado
            if payload['feedBack'] in [1, -2]:
                colecao.update_one({"idIncremental": id_inc}, {"$set": {"inserted": True}})
                print(f"✅ Feedback {payload['feedBack']} para ID {id_inc}")

            # Caso 2: Dado Inválido (Mover para Outliers)
            elif payload['feedBack'] == -1:
                doc = colecao.find_one({"idIncremental": id_inc})
                if doc:
                    colecao.delete_one({"idIncremental": id_inc})
                    db[outlier_nome].insert_one(doc)
                    print(f"❌ Documento {id_inc} movido para outliers.")

        except (pymongo.errors.AutoReconnect, pymongo.errors.NotPrimaryError):
            print("⚠️ Conexão com Primary perdida. Reatribuindo...")
            if connect_to_mongo():
                # Tenta processar a mesma mensagem uma segunda vez
                on_message(client, userdata, msg)
            
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

def connect():
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        print("A iniciar captura de feedbacks...")
        mqtt_client.connect(mqtt_broker, mqtt_port, 60)
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("\n🛑 Script terminado.")
    finally:
        if clientMongoDB:
            clientMongoDB.close()

if __name__ == "__main__":
    connect()