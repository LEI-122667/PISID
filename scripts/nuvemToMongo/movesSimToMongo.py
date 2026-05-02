from simToMongoDB import simToMongoDB
import json
import pymongo
import paho.mqtt.client as mqtt

class movesSimToMongo(simToMongoDB):
    def __init__(self, topic):
        super().__init__(topic)

    def on_message(self, client, userdata, msg):
        try:
            # Converter a mensagem recebida para dicionário Python
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

            payload['inserted'] = False
            payload['timeSent'] = None
            payload['idIncremental'] = self.getId("sensor_movimento")

            colecao.insert_one(payload)
            print(f"💾 [{tipo}] Jogador {payload.get('Player')}: ID: {payload.get('idIncremental')} \
                  RoomOrigin: {payload.get('RoomOrigin')} RoomDestiny: {payload.get('RoomDestiny')}   ")


        except Exception as e:
            print(f"Erro ao processar mensagem no tópico {msg.topic}: {e}")

def main():
    topic = "pisid_mazemov_2"
    sim_to_mongo = movesSimToMongo(topic)
    sim_to_mongo.connectToMongoDB()
    sim_to_mongo.connect()

if __name__ == "__main__":
    main()