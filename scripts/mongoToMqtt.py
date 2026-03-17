import json
from time import sleep
import pymongo
import paho.mqtt.client as mqtt
import os
from datetime import datetime, timezone, timedelta
from bson.objectid import ObjectId

#URI com as credenciais root:root e porto 27017 (padrão do MongoDB).
# https://www.emqx.com/en/blog/introduction-to-mqtt-qos
# https://www.mongodb.com/pt-br/docs/manual/reference/method/ObjectId/
uri = "mongodb://root:root@localhost:27017/"
timeout = 2000  # Tempo de espera - 2 segundos.
pisid = "pisid_maze_db"
collectionTeste = "teste"
message = {"mensagem": "Enviado do Visual Studio", "status": "OK"}
db = None  # Variável global para a base de dados, para ser usada na função de callback do MQTT.

###############-----Ligção a mongoDB-----###############

#Try except caso mongoDB não esteja a correr ou as credenciais estejam erradas.
try:

    #Estabelece a ligação, com um timeout.
    clientMongoDB = pymongo.MongoClient(uri, timeout)
    
    # Testar se o servidor responde.
    clientMongoDB.server_info() 
    print("\nLigação ao MongoDB estabelecida com sucesso!\n")

except Exception as e:
    print(f"Erro: {e}")


###############-----Ligção a MQTT-----###############

# Broker indicado no enunciado do projeto
MQTT_BROKER = "broker.hivemq.com" 
MQTT_PORT = 1883

# Uso de '#' (wildcard) para ouvir todos os jogadores (n)
TOPICO ="pisid_grupo2_dadosFiltrados"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ MQTT: Ligado ao Broker {MQTT_BROKER}")
    else:
        print(f"MQTT: Erro código {rc}")

def on_publish_callback(client, userdata, mid):
    # Esta função é chamada internamente pela biblioteca após cada envio
    pass

NOME_FICHEIRO = "lastReadDate.txt"

def ler_ultima_data():
    if not os.path.exists(NOME_FICHEIRO):
        return None
    with open(NOME_FICHEIRO, "r") as f:
        conteudo = f.read().strip()
        if not conteudo:
            return None
        # Converte a string de volta para objeto datetime (UTC)
        return datetime.fromisoformat(conteudo)
    
def escrever_ultima_data(dt):
    with open(NOME_FICHEIRO, "w") as f:
        dt_clean = dt.replace(microsecond=0)
        f.write(dt_clean.isoformat())

def publishData(client):

    while True:
        try:

            ultima_data_ficheiro = ler_ultima_data()
            maior_data_iteracao = ultima_data_ficheiro
            
            
            db = clientMongoDB[pisid]
            collections = db.list_collection_names()
            for collection_name in collections:

                print(f"📂 Coleção encontrada: {collection_name}")

                if ultima_data_ficheiro:
                    # Cria um ID falso que representa o tempo exato do ficheiro
                    data_proximo_segundo = ultima_data_ficheiro + timedelta(seconds=1)
                    id_limite = ObjectId.from_datetime(data_proximo_segundo)
                    query = {"_id": {"$gt": id_limite}}
                else:
                    query = {}

                data = list(db[collection_name].find(query))
                #data = list(db[collection_name].find({}, {"_id": 0}))  # Exclui o campo _id

                for document in data:
                    obj_id = document.get("_id")
                    if not obj_id: continue
                    data_doc = obj_id.generation_time # Já é UTC Aware

                    print(f"📅 Timestamp do ObjectId: {obj_id.generation_time}")

                        
                    # Guardar a maior data encontrada nesta volta para atualizar o ficheiro depois
                    if maior_data_iteracao is None or data_doc > maior_data_iteracao:
                        maior_data_iteracao = data_doc

                    # --- Lógica de Envio ---
                    document.pop("_id")
                    payload = json.dumps(document)
                    result = client.publish(TOPICO, payload, qos=1)  # QoS 1 para garantir entrega
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        print(f"📤 Novo dado enviado ({data_doc})")
                    else:
                        print(f"❌ Erro ao enviar dado: {mqtt.error_string(result.rc)}")
                    
                if not data:
                    print("⚠️ Nenhum dado encontrado para publicar.")



            if maior_data_iteracao and maior_data_iteracao != ultima_data_ficheiro:
                escrever_ultima_data(maior_data_iteracao)
                print(f"💾 Estado guardado: {maior_data_iteracao}")

            sleep(5)  # Espera 5 segundos antes de ler e publicar novamente
        except Exception as e:
            sleep(5)  # Espera um pouco antes de tentar novamente
            print(f"Erro ao publicar dados: {e}")

mqtt_client = mqtt.Client(transport="tcp")
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish_callback

try:
    print("A iniciar envio de dados...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    publishData(mqtt_client)
    mqtt_client.loop_stop()
except KeyboardInterrupt:
    print("\n🛑 Script terminado pelo utilizador.")
finally:
    clientMongoDB.close()