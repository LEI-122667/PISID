from mongoToMqtt import mongoToMqtt

class movesToMqtt(mongoToMqtt):
    def __init__(self,  topic, collection_name, outlier_collection_name):
        super().__init__(topic, collection_name, outlier_collection_name)
        self.corredores = None
        self.setup = None

    def isOutlier(self, doc):
        roomOriginal = doc.get('origin')
        roomDestino = doc.get('destination')
        nMarsami = doc.get('numbermarsamis')
        #RoomOriginal e RoomDestino não podem ser iguais, so se forem as duas 0
        if (roomOriginal == roomDestino and roomOriginal != 0):
            self.motivo_outlier = "RoomOriginal e RoomDestino são iguais"
            return True
        #O corredor deve existir
        corredor = self.corredores_col.find_one({
            "origin": roomOriginal, 
            "destination": roomDestino
        })

        if not corredor:
            self.motivo_outlier = f"Corredor não existe, RoomOriginal: {roomOriginal}, RoomDestino: {roomDestino}"
            return True
        
        #Marsami associado ao move é inexistente
        numMarsami = doc.get('Marsami')
        if numMarsami == None or numMarsami < 1 or numMarsami > nMarsami:
            self.motivo_outlier = "Número de Marsami inválido"
            return True
        
        return False
    
    def fetchInfoFromMongoDB(self):
        setupCollection = self.db["setup"]
        self.setup = setupCollection.find()
        self.corredores = self.db["corredores"]

def main():
    topic = "pisid_2_moves"
    collection_name = "sensor_movimento"
    outlier_collection_name = "outliers_DadosErrados_movimentos"
    temp_to_mqtt = movesToMqtt(topic, collection_name, outlier_collection_name)
    temp_to_mqtt.connectToMongoDB()
    temp_to_mqtt.fetchInfoFromMongoDB()
    temp_to_mqtt.sendingLoop()

if __name__ == "__main__":
    main()