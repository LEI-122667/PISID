import time
import os
import threading
import json
import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error

class gameAgent:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'agente_user',
            'password': 'agente',
            'database': 'bd_pisid',
            'autocommit': True
        }
        
        self.id = None
        self.last_id_file = os.path.join(os.path.dirname(__file__), 'last_id.txt')

        self.mqttBroker = "broker.hivemq.com"
        self.mqttPort = 1883
        self.mqttTopic = "pisid_mazeact"
        
        self.setMqtt()
        try:
            self.mqtt_client.connect(self.mqttBroker, self.mqttPort)
        except Exception as e:
            print(f"❌ Erro ao ligar ao Broker MQTT: {e}")
            
        self.som_lock = threading.Lock()

    def readID(self):
        if os.path.exists(self.last_id_file):
            try:
                with open(self.last_id_file, 'r') as f:
                    content = f.read().strip()
                    self.id = int(content) if content else 0
            except Exception:
                print("⚠️ Erro ao ler last_id.txt, a assumir 0")
                self.id = 0
        else:
            self.id = 0
        return self.id
    
    def writeID(self, new_id):
        try:
            with open(self.last_id_file, 'w') as f:
                f.write(str(new_id))
        except Exception:
            print("❌ Erro ao escrever last_id.txt")

    def setMqtt(self):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_publish = self.on_publish_callback
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ MQTT: Ligado ao Broker {self.mqttBroker}")
        else:
            print(f"❌ MQTT: Erro código {rc}")

    def on_publish_callback(self, client, userdata, mid):
        pass
    
    def sendAction(self, payload):
        try:
            msg = json.dumps(payload)
            self.mqtt_client.publish(self.mqttTopic, msg)
            print(f"✉️ MQTT Enviado: {msg}")
        except Exception as e:
            print(f"❌ Erro MQTT: {e}")
    
    def get_connection(self):
        return mysql.connector.connect(**self.db_config)

    def handle_som_alert(self, id_simulacao, config, setup):
        conn = None
        with self.som_lock:
            try:
                conn = self.get_connection()
                cursor = conn.cursor(dictionary=True)
            
                print("[Som] 🔊 Alerta detetado: Fechar todos os corredores...")
                cursor.callproc("Fechar_Abrir_TodosCorredores", (1,))
                for _ in cursor.stored_results(): pass
                conn.commit()
            
                self.sendAction({"Type": "CloseAllDoor", "Player": 2})

                time_fechar = config['time_fecharcorredores']
                ruido_limite = float(config['ruidolimite_fecharcorredores'])

                if time_fechar > 0:
                    print(f"[Som] Aguardar {time_fechar} segundos...")
                    time.sleep(time_fechar)
                elif ruido_limite > 0:
                    total_noise = float(setup['NormalNoise']) + float(setup['NoiseVarToleration'])
                    if ruido_limite > 1.0:
                        ruido_limite = ruido_limite / 100.0
                    
                    threshold = total_noise * ruido_limite
                    print(f"[Som] Aguardar som descer até {threshold:.2f}")
                
                    while True:
                        time.sleep(2)
                        cursor.execute("SELECT Som FROM Som WHERE IDSimulacao = %s ORDER BY IDSom DESC LIMIT 1", (id_simulacao,))
                        row = cursor.fetchone()
                        if row and float(row['Som']) <= threshold:
                            print(f"[Som] Nível seguro atingido ({row['Som']}).")
                            break

                print("[Som] Abrir todos os corredores...")
                cursor.callproc("Fechar_Abrir_TodosCorredores", (0,))
                for _ in cursor.stored_results(): pass
                conn.commit()
            
                self.sendAction({"Type": "OpenAllDoor", "Player": 2})

            except Exception as e:
                print(f"[Som Error] {e}")
            finally:
                if conn and conn.is_connected():
                    conn.close()

    def publishData(self):
        last_id = self.readID()
        while True: 
            conn = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor(dictionary=True)

                cursor.callproc("Ler_Alertas", (last_id,))
                result = []
                for rs in cursor.stored_results():
                    result.extend(rs.fetchall())
                
                if not result:
                    conn.close()
                    time.sleep(2)
                    continue
                
                row = result[0]
                
                if 'Result' in row:
                    if row['Result'] == -1:
                        print("⏳ Sem simulação ativa...")
                        conn.close()
                        time.sleep(2)
                        continue
                    elif row['Result'] == 0:
                        print("❌ Erro no Stored Procedure Ler_Alertas!")
                        conn.close()
                        time.sleep(2)
                        continue

                msg_id = row['ID']
                last_id = msg_id
                self.writeID(last_id)
                
                id_simulacao = row['IDSimulacao']
                sensor = str(row['Sensor']).strip()
                sala = row['Sala']
                
                print(f"🔔 [Alerta] ID: {msg_id} | Sensor: {sensor} | Sala: {sala}")
                
                cursor.execute("SELECT * FROM ConfigJogo WHERE IDSimulacao = %s LIMIT 1", (id_simulacao,))
                config = cursor.fetchone()
                cursor.execute("SELECT * FROM SetupMaze WHERE IDSimulacao = %s LIMIT 1", (id_simulacao,))
                setup = cursor.fetchone()

                if not config or not setup:
                    print("[-] Erro: Configurações não encontradas.")
                    conn.close()
                    continue
                
                if sensor == '2': # Som
                    t = threading.Thread(target=self.handle_som_alert, args=(id_simulacao, config, setup))
                    t.daemon = True
                    t.start()
                
                elif sensor == '1': # Temperatura
                    leitura = float(row.get('Leitura', 0))
                    high_limit = float(setup['NormalTemperature']) + float(setup['TemperatureVarHighToleration'])
                    low_limit = float(setup['NormalTemperature']) - float(setup['TemperatureVarLowToleration'])
                    
                    if abs(leitura - high_limit) < abs(leitura - low_limit):
                        print("[Temp] Ligar AC")
                        cursor.callproc("Desligar_Ligar_ArCondicionado", (1,))
                        self.sendAction({"Type": "AcOn", "Player": 2})
                    else:
                        print("[Temp] Desligar AC")
                        cursor.callproc("Desligar_Ligar_ArCondicionado", (0,))
                        self.sendAction({"Type": "AcOff", "Player": 2})
                    
                    for _ in cursor.stored_results(): pass
                    conn.commit()
                
                elif sensor == '0': # Movimento
                    if int(sala) != 0:
                        is_som_locked = self.som_lock.locked()
                        
                        if not is_som_locked:
                            cursor.execute("SELECT IDCorridor, RoomA, RoomB FROM Corridor WHERE (RoomA = %s OR RoomB = %s) AND IDSimulacao = %s", (sala, sala, id_simulacao))
                            corredores = cursor.fetchall()
                            for c in corredores:
                                cursor.callproc("Fechar_Abrir_Corredor", (c['IDCorridor'], 1))
                                self.sendAction({"Type": "CloseDoor", "Player": 2, "RoomOrigin": c['RoomA'], "RoomDestiny": c['RoomB']})
                            for _ in cursor.stored_results(): pass
                            conn.commit()

                        # Ativar Gatilhos
                        for _ in range(config.get('amount_of_gatilhos', 3)):
                            cursor.callproc("Ativar_Gatilho", (sala, 1))
                            self.sendAction({"Type": "Score", "Player": 2, "Room": sala})
                        for _ in cursor.stored_results(): pass
                        conn.commit()
                        
                        if not is_som_locked:
                            time.sleep(1) 
                            for c in corredores:
                                cursor.callproc("Fechar_Abrir_Corredor", (c['IDCorridor'], 0))
                                self.sendAction({"Type": "OpenDoor", "Player": 2, "RoomOrigin": c['RoomA'], "RoomDestiny": c['RoomB']})
                            for _ in cursor.stored_results(): pass
                            conn.commit()
                    else:
                        print("🏁 Fim de Jogo ou Entrada (Sala 0).")

            except Exception as e:
                print(f"❌ [Erro Loop Principal] {e}")
                time.sleep(2)
            finally:
                if conn and conn.is_connected():
                    conn.close()
            
            time.sleep(1)

    def mainLoop(self):  
        try:
            print("🚀 Agente iniciado...")
            self.mqtt_client.loop_start()
            self.publishData()
            self.mqtt_client.loop_stop()
        except KeyboardInterrupt:
            print("\n🛑 Script terminado pelo utilizador.")

if __name__ == "__main__":
    agent = gameAgent()
    agent.mainLoop()