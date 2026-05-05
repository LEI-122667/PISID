import mysql.connector
import paho.mqtt.client as mqtt
import json
import time

# --- Configurações ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC_ACT = "pisid_mazeact"
PLAYER_ID = 2
MYSQL_CONFIG = {
    'user': 'root',
    'password': 'password', # A que está no Docker
    'host': 'localhost',
    'database': 'bd_pisid'
}

# --- Conexão MQTT ---
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.connect(MQTT_BROKER, 1883, 60)

def enviar_comando(payload):
    mensagem = json.dumps(payload)
    mqtt_client.publish(MQTT_TOPIC_ACT, mensagem)
    print(f" Comando enviado: {mensagem}")

def verificar_regras():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # 1. REGRA DO GATILHO (Odd == Even)
        # Verifica salas onde o número de Marsamis é igual e ainda há gatilhos
        cursor.execute("SELECT Sala, Gatilho FROM OcupacaoLabirinto WHERE NumeroMarsamisOdd = NumeroMarsamisEven AND NumeroMarsamisOdd > 0 AND Gatilho > 0")
        salas_pontuar = cursor.fetchall()

        for row in salas_pontuar:
            enviar_comando({"Type": "Score", "Player": PLAYER_ID, "Room": row['Sala']})
            # Atualizar a BD para gastar um gatilho
            cursor.execute("UPDATE OcupacaoLabirinto SET Gatilho = Gatilho - 1 WHERE Sala = %s", (row['Sala'],))
            conn.commit()

        # 2. REGRA DA TEMPERATURA (Ar Condicionado)
        # Vamos buscar os limites à tabela SetupMaze da simulação ativa mais recente
        cursor.execute("""
            SELECT S.NormalTemperature, S.TemperatureVarHighToleration 
            FROM SetupMaze S
            JOIN Simulacao Sim ON S.IDSimulacao = Sim.IDSimulacao
            WHERE Sim.Ativo = TRUE
            ORDER BY Sim.IDSimulacao DESC
            LIMIT 1
        """)
        setup = cursor.fetchone()

        if setup:
            t_max = setup['NormalTemperature'] + setup['TemperatureVarHighToleration']
            cursor.execute("SELECT Temperatura FROM Temperatura ORDER BY IDTemperatura DESC LIMIT 1")
            ultima_temp = cursor.fetchone()

            if ultima_temp and float(ultima_temp['Temperatura']) > t_max:
                enviar_comando({"Type": "AcOn", "Player": PLAYER_ID})
            elif ultima_temp and float(ultima_temp['Temperatura']) <= setup['NormalTemperature']:
                enviar_comando({"Type": "AcOff", "Player": PLAYER_ID})

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Erro ao verificar regras: {e}")

# --- Loop Principal ---
print(" Sistema de Atuadores Ativo...")
while True:
    verificar_regras()
    time.sleep(2) # Verifica a cada 2 segundos