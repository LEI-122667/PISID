import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
import json

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

        # O ping garante que se a ligação caiu, ela é restabelecida antes de tentar usar o cursor.
        if not connection.is_connected():
            connection.ping(reconnect=True, attempts=3, delay=2)

        # Usamos dictionary=True para que os resultados venham como dicionários (ex: row['Result']).
        cursor = connection.cursor(dictionary=True)

        # Mapeamento de campos baseado no JSON do MongoDB (payload_doc)
        # Adaptado para a Stored Procedure de Temperatura (ajusta o nome se necessário)
        args = (
            payload.get("idIncremental"),          # MongoId (já convertido para string no script de envio)
            payload.get("Hour"),         # Hora
            payload.get("Temperature")   # Valor da Temperatura
        )

        # Executa o Stored Procedure (Certifica-te que o nome está correto na tua BD)
        # Se a SP for Inserir_Medicao_Temperatura(id, data, valor)
        cursor.callproc("Inserir_Temperatura", args)

        # Capturar o resultado do SP
        result_value = 0
        for result in cursor.stored_results():
            row = result.fetchone()
            if row and 'feedBack' in row:
                result_value = row['feedBack']

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
mqtt_client = mqtt.Client() # Removido transport="tcp" por ser o padrão e evitar avisos
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