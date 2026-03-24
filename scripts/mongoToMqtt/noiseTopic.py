import json
from time import sleep
import pymongo
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from collections import deque

JANELA_MEDIA = 5
LIMITE_VARIACAO = 20.0 
ultimas_leituras = deque(maxlen=JANELA_MEDIA)

#URI com as credenciais root:root e porto 27017 (padrão do MongoDB).
# https://www.emqx.com/en/blog/introduction-to-mqtt-qos
# https://www.mongodb.com/pt-br/docs/manual/reference/method/ObjectId/
uri = "mongodb://root:root@localhost:27017/"
timeout = 2000  # Tempo de espera - 2 segundos.
bd_name = "pisid_maze_db"
collection_name = "sensor_ruido"
outlier_collection_name = "outliers_ruido"

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

TOPICO ="pisid_grupo2_sensor_ruido"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ MQTT: Ligado ao Broker {MQTT_BROKER}")
    else:
        print(f"MQTT: Erro código {rc}")

def on_publish_callback(client, userdata, mid):
    # Esta função é chamada internamente pela biblioteca após cada envio
    pass

def publishData(client):
    global ultimas_leituras

    while True:
        try:
            db = clientMongoDB[bd_name]
            collection = db[collection_name]
            outlier_col = db[outlier_collection_name]
            
            # Busca documentos não processados ordenados por tempo (ObjectId)
            unread_documents = list(collection.find({"lido": False}).sort("_id", pymongo.ASCENDING))
            
            for doc in unread_documents:
                ruido_atual = doc.get("Sound")
                is_outlier = False
                motivo = ""

                if ruido_atual is not None:

                    if len(ultimas_leituras) > 0:
                        media_atual = sum(ultimas_leituras) / len(ultimas_leituras)
                        variacao = abs(ruido_atual - media_atual)
                        
                        if variacao > LIMITE_VARIACAO:
                            is_outlier = True
                            motivo = f"Pico de ruído suspeito: {variacao:.2f} dB de diferença da média"

                # --- Tratamento de Outliers ---
                if is_outlier:
                    print(f"❌ RUIDO OUTLIER: {ruido_atual} dB | {motivo}")
                    doc['motivo_outlier'] = motivo
                    doc['data_filtro'] = datetime.now(timezone.utc)
                    outlier_col.insert_one(doc)
                    collection.delete_one({"_id": doc["_id"]})
                    continue 

                # --- Dado Válido ---
                ultimas_leituras.append(ruido_atual)
                
                # Preparar para envio (converter ObjectId para string)
                payload_doc = doc.copy()
                payload_doc["_id"] = str(payload_doc["_id"])
                payload = json.dumps(payload_doc, default=str)
                
                client.publish(TOPICO, payload, qos=1)
                
                # Marcar como lido na BD original
                collection.update_one(
                    {"_id": doc["_id"]}, 
                    {"$set": {
                        "lido": True, 
                        "tempoQuandoFoiLido": datetime.now(timezone.utc)
                    }}
                )
                print(f"📤 Ruído enviado: {ruido_atual} dB")

            sleep(1)
        except Exception as e:
            print(f"Erro ao publicar ruído: {e}")
            sleep(5)

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