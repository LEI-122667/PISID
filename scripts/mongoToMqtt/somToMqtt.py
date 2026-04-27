from mongoToMqtt import mongoToMqtt

class somToMqtt(mongoToMqtt):
    def __init__(self, var,  topic, collection_name, outlier_collection_name):
        super().__init__(topic, collection_name, outlier_collection_name)
        self.var = var
    def isOutlier(self, doc):
        sound_value = doc.get('Sound')
        if sound_value is not None:
            media = self.getJanelaAverage()
            if media is not None and sound_value > media + self.var:
                self.motivo_outlier = f"Variação de som excede a média móvel ({media:.2f}) em mais de {self.var} DB"
                return True
            self.janela.append(sound_value)
        return False
    

def main():
    topic = "pisid_2_som"
    collection_name = "sensor_ruido"
    outlier_collection_name = "outliers_DadosErrados_ruido"
    var = 10  # Exemplo de variação para considerar um outlie
    som_to_mqtt = somToMqtt(var, topic, collection_name, outlier_collection_name)
    som_to_mqtt.connectToMongoDB()
    som_to_mqtt.sendingLoop()

if __name__ == "__main__":
    main()