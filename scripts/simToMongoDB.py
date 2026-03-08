import json
import pymongo
import paho.mqtt.client as mqtt

#
#https://pypi.org/project/pymongo/
#https://www.emqx.com/en/blog/how-to-use-mqtt-in-python#real-world-python-mqtt-examples
#
#URI com as credenciais root:root e porto 27017 (padrão do MongoDB).
uri = "mongodb://root:root@localhost:27017/"
timeout = 2000  # Tempo de espera - 2 segundos.
bdTeste = "pisid_maze_db"
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
    print("Ligação ao MongoDB estabelecida com sucesso!\n")
  
    #Criar a base de dados, uma coleção de teste e insere um documento.
    db = clientMongoDB[bdTeste]
    colecao = db[collectionTeste]
    resultado = colecao.insert_one(message)
    print(f"Documento inserido! ID: {resultado.inserted_id}")


    # Listar as DBs, coleções e o conteúdo para confirmar.
    print(f"Bases de dados: {clientMongoDB.list_database_names()}")
    print(f"Coleções em {bdTeste}: {db.list_collection_names()}")

    documentos = list(colecao.find())
    print(f"Documentos na coleção: {documentos}")

except Exception as e:
    print(f"Erro: {e}")


###############-----Ligção a MQTT-----###############

# Broker indicado no enunciado do projeto
MQTT_BROKER = "broker.hivemq.com" 
MQTT_PORT = 1883

# Uso de '#' (wildcard) para ouvir todos os jogadores (n)
TOPICOS = [
    "pisid_mazesound_2",
    "pisid_mazetemp_2",
    "pisid_mazemov_2",
    "pisid_mazeact"
]
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ MQTT: Ligado ao Broker {MQTT_BROKER}")
        for t in TOPICOS:
            try:
                # O .strip() remove qualquer lixo invisível (espaços, tabs, \r)
                filtro = t.strip()
                client.subscribe(filtro)
                print(f"📡 Subscrito com sucesso em: {filtro}")
            except Exception as e:
                print(f"❌ Erro ao subscrever a {t}: {e}")
    else:
        print(f"MQTT: Erro código {rc}")

def on_message(client, userdata, msg):
    try:
        # Converter a mensagem recebida para dicionário Python
        raw_payload = msg.payload.decode().replace("'", '"')
        payload = json.loads(raw_payload)

        topico = msg.topic
        
        # Identificar o tipo de dado pelo tópico para guardar na coleção certa
        if "sound" in topico:
            colecao = db['sensor_ruido']
            tipo = "RUÍDO"
        elif "temp" in topico:
            colecao = db['sensor_temperatura']
            tipo = "TEMP"
        elif "mov" in topico:
            colecao = db['sensor_movimento']
            tipo = "MOV"
        else:
            colecao = db['acoes_jogo']
            tipo = "AÇÃO"

        # Inserir no MongoDB
        # O MongoDB vai guardar o campo 'Player' que já vem no JSON do simulador
        colecao.insert_one(payload)
        
        print(f"💾 [{tipo}] Jogador {payload.get('Player')}: {payload}")

    except Exception as e:
        print(f"Erro ao processar mensagem no tópico {msg.topic}: {e}")

mqtt_client = mqtt.Client(transport="tcp")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    print("A iniciar captura de dados...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    print("\n🛑 Script terminado pelo utilizador.")
finally:
    clientMongoDB.close()