import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

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

# ✅ Valida e converte o datetime — retorna None se inválido
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
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
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

        # Se o datetime for inválido, envia -1 para feedback imediatamente
        if hora is None:
            print(f"⚠️ MQTT: Datetime inválido '{payload.get('Hour')}' — a enviar feedBack -1")
            payload["feedBack"] = -1
            feedback_payload = json.dumps(payload)
            client.publish(MQTT_TOPIC_FEEDBACK, feedback_payload)
            print(f"✉️ MQTT: Feedback enviado ({MQTT_TOPIC_FEEDBACK}): {feedback_payload}")
            return

        # Garantir a conexão à BD (Caso o MySQL feche a conexão por inatividade)
        if not connection.is_connected():
            connection.ping(reconnect=True, attempts=3, delay=2)

        # O cursor é o "navegador" que executa os comandos na BD
        cursor = connection.cursor(dictionary=True)

        args = (
            payload.get("idIncremental"),   # ID vindo do MongoDB
            hora,                           # Hora validada
            payload.get("Sound")            # Valor do ruído em dB
        )

        print(f"🔍 Args enviados para SP: {args}")

        # Executa a Stored Procedure para inserir medição de ruído
        cursor.callproc("Inserir_Som", args)

        # Capturar o resultado (Result) devolvido pela SP
        result_value = 0
        for result in cursor.stored_results():
            row = result.fetchone()
            if row and 'Result' in row:
                result_value = row['Result']

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