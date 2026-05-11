import time
import os
import threading
import json
import paho.mqtt.client as mqtt
import mysql.connector

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────
LAST_ID_FILE = os.path.join(os.path.dirname(__file__), 'last_id.txt')
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "pisid_mazeact"
DEBUG = True


# ─────────────────────────────────────────────
# SCHEMA DEFINITIONS
# ─────────────────────────────────────────────
MESSAGE_SCHEMAS = {
    "Score": ["Type", "Player", "Room"],
    "OpenDoor": ["Type", "Player", "RoomOrigin", "RoomDestiny"],
    "CloseDoor": ["Type", "Player", "RoomOrigin", "RoomDestiny"],
    "CloseAllDoor": ["Type", "Player"],
    "OpenAllDoor": ["Type", "Player"],
    "AcOn": ["Type", "Player"],
    "AcOff": ["Type", "Player"]
}


class AgenteJogo:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'agente_user',
            'password': 'agente',
            'database': 'bd_pisid',
            'autocommit': True
        }

        self.mqtt_connected = threading.Event()
        self.som_lock = threading.Lock()
        self.last_id = self.load_last_id()

        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except:
            self.client = mqtt.Client()

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    # ─────────────────────────────────────────────
    # PERSISTÊNCIA
    # ─────────────────────────────────────────────
    def load_last_id(self):
        if os.path.exists(LAST_ID_FILE):
            try:
                with open(LAST_ID_FILE, 'r') as f:
                    return int(f.read().strip())
            except:
                pass
        return 0

    def save_last_id(self, last_id):
        try:
            with open(LAST_ID_FILE, 'w') as f:
                f.write(str(last_id))
        except Exception as e:
            print(f"⚠️ Erro ao salvar last_id: {e}")

    def get_db_connection(self):
        return mysql.connector.connect(**self.db_config)

    # ─────────────────────────────────────────────
    # MQTT
    # ─────────────────────────────────────────────
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ MQTT ligado a {MQTT_BROKER}")
            self.mqtt_connected.set()

    def on_disconnect(self, client, userdata, rc):
        print("⚠️ MQTT desconectado")
        self.mqtt_connected.clear()

    def format_payload_custom(self, payload):
        t = payload["Type"]
        p = payload["Player"]

        if t == "Score":
            return f"{{Type: Score, Player:{p}, Room: {payload['Room']}}}"

        elif t == "OpenDoor":
            return f"{{Type: OpenDoor, Player:{p}, RoomOrigin: {payload['RoomOrigin']}, RoomDestiny: {payload['RoomDestiny']}}}"

        elif t == "CloseDoor":
            return f"{{Type: CloseDoor, Player:{p}, RoomOrigin: {payload['RoomOrigin']}, RoomDestiny: {payload['RoomDestiny']}}}"

        elif t == "CloseAllDoor":
            return f"{{Type: CloseAllDoor, Player:{p}}}"

        elif t == "OpenAllDoor":
            return f"{{Type: OpenAllDoor, Player:{p}}}"

        elif t == "AcOn":
            return f"{{Type: AcOn, Player:{p}}}"

        elif t == "AcOff":
            return f"{{Type: AcOff, Player:{p}}}"

        else:
            raise ValueError(f"Tipo desconhecido: {t}")

    # ─────────────────────────────────────────────
    # VALIDATION + NORMALIZATION
    # ─────────────────────────────────────────────
    def validate_payload(self, payload):
        msg_type = payload.get("Type")

        if msg_type not in MESSAGE_SCHEMAS:
            print(f"❌ Tipo inválido: {msg_type}")
            return False

        required = MESSAGE_SCHEMAS[msg_type]

        # Missing fields
        for field in required:
            if field not in payload:
                print(f"❌ Campo em falta ({msg_type}): {field}")
                return False

        # Extra fields (strict mode)
        for field in payload.keys():
            if field not in required:
                print(f"⚠️ Campo extra ignorado: {field}")

        return True

    def normalize_payload(self, payload):
        """Force correct types"""
        payload["Type"] = str(payload["Type"])
        payload["Player"] = int(payload["Player"])

        if "Room" in payload:
            payload["Room"] = int(payload["Room"])

        if "RoomOrigin" in payload:
            payload["RoomOrigin"] = int(payload["RoomOrigin"])

        if "RoomDestiny" in payload:
            payload["RoomDestiny"] = int(payload["RoomDestiny"])

        return payload

    def send_mqtt(self, payload):
        if not self.mqtt_connected.is_set():
            print("❌ MQTT sem ligação")
            return False

        payload = self.normalize_payload(payload)

        if not self.validate_payload(payload):
            print(f"❌ Payload inválido: {payload}")
            return False

        try:
            msg = self.format_payload_custom(payload)
        except Exception as e:
            print(f"❌ Erro a formatar payload: {e}")
            return False

        print(f"📤 MQTT -> {msg}")

        result = self.client.publish(MQTT_TOPIC, msg, qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    # ─────────────────────────────────────────────
    # HANDLERS
    # ─────────────────────────────────────────────
    def handle_som(self, id_sim, config, setup):
        with self.som_lock:
            conn = None
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor(dictionary=True)

                cursor.callproc("Fechar_Abrir_TodosCorredores", (1,))
                self.send_mqtt({"Type": "CloseAllDoor", "Player": 2})

                limite_percentagem = float(config.get('ruidolimite_fecharcorredores', 0))
                tempo_espera = int(config.get('time_fecharcorredores', 0))

                if limite_percentagem > 0:
                    normal = float(setup.get('NormalNoise', 0))
                    toleration = float(setup.get('NoiseVarToleration', 0))
                    total_limit = normal + toleration
                    target_sound = total_limit * (limite_percentagem / 100.0)
                    
                    print(f"🔊 [Som] A aguardar que o som baixe de {target_sound:.2f} (Total={total_limit}, Limite={limite_percentagem}%)")
                    
                    while True:
                        cursor.execute("SELECT Som FROM Som WHERE IDSimulacao = %s ORDER BY IDSom DESC LIMIT 1", (id_sim,))
                        row = cursor.fetchone()
                        if row and row['Som'] is not None:
                            current_sound = float(row['Som'])
                            if current_sound < target_sound:
                                print(f"🔊 [Som] Som atual ({current_sound}) baixou do limite ({target_sound}). A reabrir portas.")
                                break
                        time.sleep(1)
                else:
                    print(f"🔊 [Som] A aguardar {tempo_espera}s (modo tempo)")
                    time.sleep(tempo_espera)

                cursor.callproc("Fechar_Abrir_TodosCorredores", (0,))
                self.send_mqtt({"Type": "OpenAllDoor", "Player": 2})

            except Exception as e:
                print(f"❌ Som: {e}")
            finally:
                if conn:
                    conn.close()

    def handle_temperatura(self, row, setup, cursor):
        leitura = float(row.get('Leitura', 0))
        normal = float(setup.get('NormalTemperature', 0))

        if leitura > normal:
            cursor.callproc("Desligar_Ligar_ArCondicionado", (1,))
            self.send_mqtt({"Type": "AcOn", "Player": 2})
        else:
            cursor.callproc("Desligar_Ligar_ArCondicionado", (0,))
            self.send_mqtt({"Type": "AcOff", "Player": 2})

    def handle_movimento(self, row, config, id_sim, cursor):
        sala = int(row['Sala'])
        if sala == 0:
            return

        is_locked = self.som_lock.locked()

        # Obter os corredores ligados à sala
        corredores_da_sala = []
        if not is_locked:
            cursor.execute("SELECT IDCorridor, RoomA, RoomB FROM Corridor WHERE IDSimulacao = %s AND (RoomA = %s OR RoomB = %s)", (id_sim, sala, sala))
            corredores_da_sala = cursor.fetchall()

        # ─────────────────────────────
        # 1. CLOSE PORTAS DA SALA
        # ─────────────────────────────
        modo_fecho = int(config.get('modo_fecho_portas', 0))

        if not is_locked:
            if modo_fecho == 1:
                print(f"🚪 [Movimento] Fechar TODOS os corredores (Odd=Even)")
                cursor.callproc("Fechar_Abrir_TodosCorredores", (1,))
                self.send_mqtt({"Type": "CloseAllDoor", "Player": 2})
            else:
                print(f"🚪 [Movimento] Fechar portas ligadas à sala {sala}")
                for c in corredores_da_sala:
                    cursor.callproc("Fechar_Abrir_Corredor", (c['IDCorridor'], 1))
                    self.send_mqtt({
                        "Type": "CloseDoor",
                        "Player": 2,
                        "RoomOrigin": c['RoomA'],
                        "RoomDestiny": c['RoomB']
                    })

            # 🔴 IMPORTANT: wait for server to apply state
            if modo_fecho == 1 or corredores_da_sala:
                time.sleep(0.5)

        # ─────────────────────────────
        # 2. TRIGGER SCORE (GATILHOS)
        # ─────────────────────────────
        amt = config.get('amount_of_gatilhos', 3)

        print(f"🎯 [Movimento] Tentar ativar até {amt} gatilhos na sala {sala}")

        activated = 0

        for _ in range(amt):
            cursor.callproc("Ativar_Gatilho", (sala, 1))

            result_value = None

            # Read SP result
            for res in cursor.stored_results():
                row_result = res.fetchone()
                if row_result and "Result" in row_result:
                    result_value = int(row_result["Result"])

            if result_value == 1:
                # ✅ Only send if DB actually applied it
                self.send_mqtt({
                    "Type": "Score",
                    "Player": 2,
                    "Room": sala
                })
                activated += 1

            elif result_value == -1:
                print(f"⛔ [Movimento] Sem mais gatilhos disponíveis (parar)")
                break

            else:
                print(f"⚠️ [Movimento] Erro ao ativar gatilho (Result={result_value})")
                break

            time.sleep(0.05)

        print(f"✅ [Movimento] Gatilhos ativados: {activated}")

        # 🔴 IMPORTANT: wait after scoring
        if activated > 0 or not is_locked:
            time.sleep(0.7)

        # ─────────────────────────────
        # 3. OPEN PORTAS DA SALA
        # ─────────────────────────────
        if not is_locked:
            if self.som_lock.locked():
                print(f"🚪 [Movimento] Abertura de portas cancelada (Alerta de Som em curso tem prioridade)")
            else:
                if modo_fecho == 1:
                    print(f"🚪 [Movimento] Reabrir TODOS os corredores")
                    cursor.callproc("Fechar_Abrir_TodosCorredores", (0,))
                    self.send_mqtt({"Type": "OpenAllDoor", "Player": 2})
                else:
                    print(f"🚪 [Movimento] Reabrir portas ligadas à sala {sala}")
                    for c in corredores_da_sala:
                        cursor.callproc("Fechar_Abrir_Corredor", (c['IDCorridor'], 0))
                        self.send_mqtt({
                            "Type": "OpenDoor",
                            "Player": 2,
                            "RoomOrigin": c['RoomA'],
                            "RoomDestiny": c['RoomB']
                        })

    # ─────────────────────────────────────────────
    # LOOP
    # ─────────────────────────────────────────────
    def run(self):
        print("🚀 Agente iniciado")

        self.client.connect(MQTT_BROKER, MQTT_PORT)
        self.client.loop_start()

        while True:
            conn = None
            try:
                if not self.mqtt_connected.wait(timeout=5):
                    continue

                conn = self.get_db_connection()
                cursor = conn.cursor(dictionary=True)

                cursor.callproc("Ler_Alertas", (self.last_id,))
                alertas = []

                for res in cursor.stored_results():
                    alertas.extend(res.fetchall())

                if not alertas:
                    time.sleep(1)
                    continue

                row = alertas[0]

                # Handle special SP responses first
                if 'Result' in row:
                    if row['Result'] == -1:
                        time.sleep(2)
                        continue
                    if row['Result'] == 0:
                        print("❌ SP Ler_Alertas erro")
                        time.sleep(2)
                        continue

                # Ensure ID exists
                if 'ID' not in row:
                    print(f"⚠️ Alerta sem ID recebido: {row}")
                    time.sleep(1)
                    continue

                # Safe to use
                self.last_id = int(row['ID'])
                self.save_last_id(self.last_id)

                id_sim = row['IDSimulacao']
                sensor = str(row['Sensor']).strip()

                cursor.execute("SELECT * FROM ConfigJogo WHERE IDSimulacao=%s", (id_sim,))
                config = cursor.fetchone()

                cursor.execute("SELECT * FROM SetupMaze WHERE IDSimulacao=%s", (id_sim,))
                setup = cursor.fetchone()

                if not config or not setup:
                    continue

                if sensor == '2':
                    threading.Thread(target=self.handle_som, args=(id_sim, config, setup), daemon=True).start()

                elif sensor == '1':
                    self.handle_temperatura(row, setup, cursor)

                elif sensor == '0':
                    self.handle_movimento(row, config, id_sim, cursor)

            except Exception as e:
                print(f"💥 Loop erro: {e}")
                time.sleep(2)
            finally:
                if conn:
                    conn.close()


if __name__ == "__main__":
    agente = AgenteJogo()
    try:
        agente.run()
    except KeyboardInterrupt:
        print("🛑 Encerrado")