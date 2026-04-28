import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

# Configurações do MySql (Usando o utilizador específico para temperatura)
usermysql = "script_temperatura"
passmysql = "temp"
hostmysql = "localhost"
database = "bd_pisid"

# Configurações do MQTT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "pisid_2_temp"
MQTT_TOPIC_FEEDBACK = "pisid_2_feedBack_temp"

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
    print(f"✅ MySQL: Conectado como {usermysql}")
except Error as e:
    print(f"❌ MySQL: Erro ao conectar: {e}")
    exit(1)

# Valida e converte o datetime — retorna None se inválido
def parse_datetime(value):
    if value is None:
        return None
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return None

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

        # Validar o datetime antes de enviar para a SP
        hora = parse_datetime(payload.get("Hour"))

        #Se o datetime for inválido, envia -1 para feedback imediatamente
        if hora is None:
            print(f"⚠️ MQTT: Datetime inválido '{payload.get('Hour')}' — a enviar feedBack -1")
            payload["feedBack"] = -1
            feedback_payload = json.dumps(payload)
            client.publish(MQTT_TOPIC_FEEDBACK, feedback_payload)
            print(f"✉️ MQTT: Feedback enviado ({MQTT_TOPIC_FEEDBACK}): {feedback_payload}")
            return  # Para aqui, não chama a SP

        # O ping garante que se a ligação caiu, ela é restabelecida antes de tentar usar o cursor.
        if not connection.is_connected():
            connection.ping(reconnect=True, attempts=3, delay=2)

        # Usamos dictionary=True para que os resultados venham como dicionários (ex: row['Result']).
        cursor = connection.cursor(dictionary=True)

        args = (
            payload.get("idIncremental"),   # MongoId
            hora,                           # Hora validada
            payload.get("Temperature")      # Valor da Temperatura
        )

        print(f"🔍 Args enviados para SP: {args}")

        cursor.callproc("Inserir_Temperatura", args)

        # Capturar o resultado do SP
        result_value = 0
        for result in cursor.stored_results():
            row = result.fetchone()
            if row and 'Result' in row:
                result_value = row['Result']

        cursor.close()

        # Atualiza o objeto original com o resultado do SP para feedback
        payload["feedBack"] = result_value

        # Envia a mensagem para o tópico de feedback
        feedback_payload = json.dumps(payload)
        client.publish(MQTT_TOPIC_FEEDBACK, feedback_payload)
        print(f"✉️ MQTT: Feedback enviado ({MQTT_TOPIC_FEEDBACK}): {feedback_payload}")

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
    print("\n🛑 PYTHON: Script terminado.")
    if connection.is_connected():
        connection.close()
        print("\n🛑 PYTHON: Base de dados desconectada.")