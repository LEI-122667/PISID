import time
import os
import threading
import json
import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error

LAST_ID_FILE = os.path.join(os.path.dirname(__file__), 'last_id.txt')

def load_last_id():
    if os.path.exists(LAST_ID_FILE):
        try:
            with open(LAST_ID_FILE, 'r') as f:
                return int(f.read().strip())
        except Exception:
            pass
    return 0

def save_last_id(last_id):
    try:
        with open(LAST_ID_FILE, 'w') as f:
            f.write(str(last_id))
    except Exception as e:
        print(f"Erro ao salvar last_id: {e}")

db_config = {
    'host': 'localhost',
    'user': 'agente_user',
    'password': 'agente',
    'database': 'bd_pisid',
    'autocommit': True
}

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_ACT = "pisid_mazeact"

# Lock global para garantir que alertas de som são processados sequencialmente
som_lock = threading.Lock()

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print(f"✅ MQTT: Conectado ao Broker {MQTT_BROKER}")
except Exception as e:
    print(f"❌ Erro ao conectar ao MQTT: {e}")

def send_mqtt_action(payload):
    try:
        msg = json.dumps(payload)
        mqtt_client.publish(MQTT_TOPIC_ACT, msg)
        print(f"✉️ MQTT Enviado: {msg}")
    except Exception as e:
        print(f"❌ Erro MQTT: {e}")

def get_connection():
    return mysql.connector.connect(**db_config)

def handle_som_alert(id_simulacao, config, setup):
    with som_lock:
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Close all corridors
            print("[Som] Fechar todos os corredores...")
            cursor.callproc("Fechar_Abrir_TodosCorredores", (1,))
            for _ in cursor.stored_results(): pass
            conn.commit()
            
            send_mqtt_action({"Type": "CloseAllDoor", "Player": 2})

            time_fechar = config['time_fecharcorredores']
            ruido_limite = float(config['ruidolimite_fecharcorredores'])

            if time_fechar > 0:
                print(f"[Som] Aguardar {time_fechar} segundos antes de abrir...")
                time.sleep(time_fechar)
            elif ruido_limite > 0:
                # Assuming fraction like 0.8
                total_noise = float(setup['NormalNoise']) + float(setup['NoiseVarToleration'])
                
                if ruido_limite > 1.0:
                    ruido_limite = ruido_limite / 100.0
                    
                threshold = total_noise * ruido_limite
                print(f"[Som] Aguardar som descer até {threshold:.2f} (Limite: {ruido_limite*100}%)")
                
                while True:
                    time.sleep(2)
                    cursor.execute("SELECT Som FROM Som WHERE IDSimulacao = %s ORDER BY IDSom DESC LIMIT 1", (id_simulacao,))
                    row = cursor.fetchone()
                    if row:
                        current_som = float(row['Som'])
                        if current_som <= threshold:
                            print(f"[Som] Som desceu para {current_som}. Abrir corredores.")
                            break
                    else:
                        # No readings yet? Wait.
                        pass

            print("[Som] Abrir todos os corredores...")
            cursor.callproc("Fechar_Abrir_TodosCorredores", (0,))
            for _ in cursor.stored_results(): pass
            conn.commit()
            
            send_mqtt_action({"Type": "OpenAllDoor", "Player": 2})

        except Exception as e:
            print(f"[Som Error] {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                conn.close()

def run_agente():
    print("Iniciar Agente Jogo...")
    last_id = load_last_id()
    print(f"Retomando a partir do ID: {last_id}")
    
    while True:
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Use Ler_Alertas
            cursor.callproc("Ler_Alertas", (last_id,))
            result = []
            for rs in cursor.stored_results():
                for row_data in rs.fetchall():
                    result.append(row_data)
            
            if not result:
                # No messages found, sleep and retry
                conn.close()
                time.sleep(1)
                continue
                
            row = result[0]
            
            # Check for error or no game
            if 'Result' in row:
                if row['Result'] == -1:
                    print("⏳ Sem simulação ativa. A aguardar...")
                    time.sleep(2)
                    conn.close()
                    continue
                elif row['Result'] == 0:
                    print("❌ Erro interno no Stored Procedure Ler_Alertas!")
                    time.sleep(2)
                    conn.close()
                    continue

            # We got a message
            msg_id = row['ID']
            last_id = msg_id
            save_last_id(last_id)
            
            id_simulacao = row['IDSimulacao']
            sensor = str(row['Sensor']).strip()
            sala = row['Sala']
            
            print(f"[Alerta] ID: {msg_id} | Sensor: {sensor} | Sala: {sala}")
            
            # Fetch config for this simulation
            cursor.execute("SELECT * FROM ConfigJogo WHERE IDSimulacao = %s LIMIT 1", (id_simulacao,))
            config = cursor.fetchone()
            
            cursor.execute("SELECT * FROM SetupMaze WHERE IDSimulacao = %s LIMIT 1", (id_simulacao,))
            setup = cursor.fetchone()

            if not config or not setup:
                print("[-] Erro: ConfigJogo ou SetupMaze não encontrados.")
                conn.close()
                continue
                
            if sensor == '2': # Som
                t = threading.Thread(target=handle_som_alert, args=(id_simulacao, config, setup))
                t.daemon = True
                t.start()
                
            elif sensor == '1': # Temperatura
                leitura = float(row.get('Leitura', 0))
                normal_temp = float(setup.get('NormalTemperature', 0))
                high_tol = float(setup.get('TemperatureVarHighToleration', 0))
                low_tol = float(setup.get('TemperatureVarLowToleration', 0))
                
                high_limit = normal_temp + high_tol
                low_limit = normal_temp - low_tol
                
                dist_high = abs(leitura - high_limit)
                dist_low = abs(leitura - low_limit)
                
                if dist_high < dist_low:
                    print(f"[Temperatura] Leitura ({leitura}) está mais próxima do limite superior ({high_limit}). Ligar Ar Condicionado...")
                    cursor.callproc("Desligar_Ligar_ArCondicionado", (1,))
                    send_mqtt_action({"Type": "AcOn", "Player": 2})
                else:
                    print(f"[Temperatura] Leitura ({leitura}) está mais próxima do limite inferior ({low_limit}). Desligar Ar Condicionado...")
                    cursor.callproc("Desligar_Ligar_ArCondicionado", (0,))
                    send_mqtt_action({"Type": "AcOff", "Player": 2})
                for _ in cursor.stored_results(): pass
                conn.commit()
                
            elif sensor == '0': # Movimento
                print(f"[Movimento] Fechar corredores da Sala {sala}...")
                cursor.execute("SELECT IDCorridor, RoomA, RoomB FROM Corridor WHERE (RoomA = %s OR RoomB = %s) AND IDSimulacao = %s", (sala, sala, id_simulacao))
                corredores = cursor.fetchall()
                
                # 1. Fechar as portas
                for c in corredores:
                    c_id = c['IDCorridor']
                    room_a = c['RoomA']
                    room_b = c['RoomB']
                    
                    cursor.callproc("Fechar_Abrir_Corredor", (c_id, 1))
                    send_mqtt_action({"Type": "CloseDoor", "Player": 2, "RoomOrigin": room_a, "RoomDestiny": room_b})
                for _ in cursor.stored_results(): pass
                conn.commit()
                
                # 2. Ativar Gatilhos e enviar MQTT
                amt_gatilhos = config.get('amount_of_gatilhos', 3)
                print(f"[Movimento] Ativar {amt_gatilhos} gatilhos na Sala {sala}...")
                cursor.callproc("Ativar_Gatilho", (sala, amt_gatilhos))
                for _ in cursor.stored_results(): pass
                conn.commit()
                
                for _ in range(amt_gatilhos):
                    send_mqtt_action({"Type": "Score", "Player": 2, "Room": sala})
                    
                time.sleep(1) # Aguarda um pouco para as portas não abrirem instantaneamente
                
                # 3. Abrir as portas novamente
                print(f"[Movimento] Abrir corredores da Sala {sala}...")
                for c in corredores:
                    c_id = c['IDCorridor']
                    room_a = c['RoomA']
                    room_b = c['RoomB']
                    
                    cursor.callproc("Fechar_Abrir_Corredor", (c_id, 0))
                    send_mqtt_action({"Type": "OpenDoor", "Player": 2, "RoomOrigin": room_a, "RoomDestiny": room_b})
                for _ in cursor.stored_results(): pass
                conn.commit()
                
        except Exception as e:
            print(f"[Error in Main Loop] {e}")
            time.sleep(2)
        finally:
            if 'conn' in locals() and conn.is_connected():
                conn.close()
        
        time.sleep(0.5)

if __name__ == "__main__":
    run_agente()
