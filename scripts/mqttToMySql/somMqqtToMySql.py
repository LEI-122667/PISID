import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
import json

# Configurações do MySql (Usando o utilizador específico para o script de som)
usermysql = "script_som"
passmysql = "som"
hostmysql = "localhost"
database = "bd_pisid"

# Configurações do MQTT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "pisid_2_som"
MQTT_TOPIC_FEEDBACK = "pisid_2_feedBack_som"

# Conexão à BD
try:
    connection = mysql.connector.connect(
        host=hostmysql,
        user=usermysql,
        password=passmysql,
        database=database,
        connect_timeout=1000,
        autocommit=True
    )
    print(f"✅ MySQL: Conectado ao {database} como {usermysql}")
except Error as e:
    print("❌ MySQL: Erro ao conectar:", e)
    exit(1)

# Conexão ao MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ MQTT: Ligado ao Broker {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
        print(f"✅ MQTT: A escutar o tópico {MQTT_TOPIC}")
    else:
        print(f"❌ MQTT: Erro código {rc}")

# Função que recebe a mensagem do MQTT e Executa SP do MySql
def on_message(client, userdata, msg):
    try:
        # Converter a mensagem recebida para Python
        raw_payload = msg.payload.decode().replace("'", '"')
        payload = json.loads(raw_payload)
        print(f"✉️ MQTT: Mensagem Recebida {payload}")

        # Garantir a conexão à BD (Caso o MySQL feche a conexão por inatividade)
        if not connection.is_connected():
            connection.ping(reconnect=True, attempts=3, delay=2)

        # O cursor é o "navegador" que executa os comandos na BD
        cursor = connection.cursor(dictionary=True)

        # Mapeamento de campos baseado no JSON enviado pelo script do MongoDB
        # Nota: O Mongo envia "idIncremental" (como string) e "Sound"
        args = (
            payload.get("idIncremental"),     # ID vindo do MongoDB
            payload.get("Hour"),    # Campo de data (garante que existe no Mongo)
            payload.get("Sound")    # Valor do ruído em dB
        )

        # Executa a Stored Procedure para inserir medição de ruído
        # Substitui "Inserir_Ruido" pelo nome exato da tua SP na BD
        cursor.callproc("Inserir_Som", args)

        # Capturar o resultado (Result) devolvido pela SP
        result_value = 0
        for result in cursor.stored_results():
            row = result.fetchone()
            if row and 'feedBack' in row:
                result_value = row['feedBack']

        cursor.close()

        # Atualiza o objeto para o feedback
        payload["feedBack"] = result_value

        # Envia feedback para o tópico central
        feedback_payload = json.dumps(payload)
        client.publish(MQTT_TOPIC_FEEDBACK, feedback_payload)
        print(f"✉️ MQTT: Feedback enviado: {feedback_payload}")

    except Exception as e:
        print(f"❌ MQTT: Erro ao processar mensagem: {e}")

# Configuração do cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    print("\n🛑 PYTHON: Script terminado pelo utilizador.")
    if connection.is_connected():
        connection.close()
        print("\n🛑 PYTHON: Base de dados desconectada.")