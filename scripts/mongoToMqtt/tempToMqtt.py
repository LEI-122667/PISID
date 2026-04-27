from mongoToMqtt import mongoToMqtt

class tempToMqtt(mongoToMqtt):
    def __init__(self, var,  topic, collection_name, outlier_collection_name):
        super().__init__(topic, collection_name, outlier_collection_name)
        self.var = var
    def isOutlier(self, doc):
        temperature_value = doc.get('Temperature')
        if temperature_value is not None:
            media = self.getJanelaAverage()
            if media is not None and temperature_value > media + self.var:
                self.motivo_outlier = f"Variação de temperatura excede a média móvel ({media:.2f}) em mais de {self.var} °C"
                return True
            elif media is not None and temperature_value < media - self.var:
                self.motivo_outlier = f"Variação de temperatura excede a média móvel ({media:.2f}) em mais de {self.var} °C para baixo"
                return True
            self.janela.append(temperature_value)
        return False
    

def main():
    topic = "pisid_2_temp"
    collection_name = "sensor_temperatura"
    outlier_collection_name = "outliers_DadosErrados_temperatura"
    var = 5  # Exemplo de variação para considerar um outlie
    temp_to_mqtt = tempToMqtt(var, topic, collection_name, outlier_collection_name)
    temp_to_mqtt.connectToMongoDB()
    temp_to_mqtt.sendingLoop()

if __name__ == "__main__":
    main()