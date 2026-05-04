from simToMongoDB import simToMongoDB
import json
import pymongo
import paho.mqtt.client as mqtt
from datetime import datetime, timezone, timedelta

class movesSimToMongo(simToMongoDB):
    def __init__(self, topic):
        super().__init__(topic)

    def on_message(self, client, userdata, msg):
        try:
            raw_payload = msg.payload.decode().replace("'", '"')
            payload = json.loads(raw_payload)

            topico = msg.topic

            if "mov" in topico:
                colecao = self.db['sensor_movimento']
                tipo = "MOV"
            else:
                print(f"⚠️ Tópico desconhecido: {topico}")
                colecao = self.db['dados_desconecidos']
                tipo = "DESCONHECIDO"
                return

            payload['idIncremental'] = self.getId("sensor_movimento")
            payload['inserted'] = False
            payload['timeSent'] = None
            portugal_tz = timezone(timedelta(hours=1))
            time_now = datetime.now(portugal_tz)
            payload["Hour"] = time_now

            success = False
            while not success:
                try:
             
                    colecao = self.db['sensor_movimento']
                    colecao.insert_one(payload)
                    print(f"💾 [MOV] Jogador {payload.get('Player')}: ID: {payload.get('idIncremental')}: Tipo: {tipo}")
                    success = True
                    
                except Exception as e:
                    print(f"⚠️ Erro de conexão detetado: {e}. A tentar reconectar...")
                    if self.connectToMongoDB():
                        print("✅ Reconectado com sucesso. A repetir inserção...")
                    else:
                        print("❌ Falha crítica: Não foi possível encontrar novo PRIMARY.")
                        break

        except Exception as e:
            print(f"Erro ao processar mensagem no tópico {msg.topic}: {e}")

def main():
    topic = "pisid_mazemov_2"
    sim_to_mongo = movesSimToMongo(topic)
    sim_to_mongo.connectToMongoDB()
    sim_to_mongo.connect()

if __name__ == "__main__":
    main()