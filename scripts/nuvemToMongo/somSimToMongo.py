from random import random

from simToMongoDB import simToMongoDB
import json
import pymongo
import paho.mqtt.client as mqtt

class somSimToMongo(simToMongoDB):
    def __init__(self, topic, file_path=None):
        super().__init__(topic, file_path   )

    def on_message(self, client, userdata, msg):
        try:
            # Converter a mensagem recebida para dicionário Python
            raw_payload = msg.payload.decode().replace("'", '"')
            payload = json.loads(raw_payload)

            topico = msg.topic

            if "sound" in topico:
                colecao = self.db['sensor_ruido']
                tipo = "SOUND"
            else:
                print(f"⚠️ Tópico desconhecido: {topico}")
                colecao = self.db['dados_desconecidos']
                tipo = "DESCONHECIDO"
                return

            payload['inserted'] = False
            payload['timeSent'] = None
            
            # 1. Move pointer to start to read the existing ID
            self.file.seek(0)
            ultimo_id = self.file.read().strip()

            # 2. Calculate the new ID
            if ultimo_id and ultimo_id.isdigit():
                payload['idIncremental'] = int(ultimo_id) + 1
            else:            
                payload['idIncremental'] = random.random() * 1000
    
            # 3. Clear the file and move pointer to start to overwrite
            self.file.seek(0)
            self.file.truncate() # Ensures the old number is fully removed
            self.file.write(str(payload['idIncremental']))

            # 4. Force write to disk (optional but safer)
            self.file.flush()
            
            try:
                colecao.insert_one(payload)
                print(f"💾 [{tipo}] Jogador {payload.get('Player')}: ID: {payload.get('idIncremental')}")
            except (pymongo.errors.AutoReconnect, pymongo.errors.NotPrimaryError, pymongo.errors.ServerSelectionTimeoutError):
                print("⚠️ Primary perdido! A re-estabelecer ligação...")
                self.connectToMongoDB()
                # Tenta inserir novamente após recuperar a ligação
                self.db['sensor_ruido'].insert_one(payload) 
                print("✅ Dado inserido com sucesso após failover.")
                
        except Exception as e:
            print(f"Erro ao processar mensagem no tópico {msg.topic}: {e}")


def main():
    topic = "pisid_mazesound_2"
    sim_to_mongo = somSimToMongo(topic, "/home/sebas/Documentos/Cadeiras/Pisid/PISID/scripts/nuvemToMongo/idSom.txt")
    sim_to_mongo.connectToMongoDB()
    sim_to_mongo.connect()

if __name__ == "__main__":
    main()