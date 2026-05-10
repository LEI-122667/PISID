from mongoToMqtt import mongoToMqtt

class tempToMqtt(mongoToMqtt):
    def __init__(self,  topic, collection_name, outlier_collection_name):
        super().__init__(topic, collection_name, outlier_collection_name)
        self.var = None
        self.connectToMongoDB()
        self.sendingLoop()

    def isOutlier(self, doc):
        if not self.fetched:
            print("⚠️ Aviso: Dados de configuração a carregados...")
            self.fetchInfoFromMongoDB()
            self.SimID = self.setup_doc.get('IDSimulacao')
            self.fetched = True
            self.var = self.setup_doc.get('outliers_temperatura')
            print(f"✅ Configuração carregada. Variação para outliers de temperatura: {self.var} °C e ID da simulação: {self.SimID}")

        if self.fetched:
            new_setup_doc = self.db["setup"].find_one()
            if new_setup_doc.get('IDSimulacao') != self.SimID:
                print("⚠️ Detetada mudança no ID da simulação. A recarregar configuração...")
                self.fetchInfoFromMongoDB()
                self.SimID = self.setup_doc.get('IDSimulacao')
                self.janela.clear()  # Limpa a janela para evitar comparações erradas com dados antigos
                self.var = self.setup_doc.get('outliers_temperatura')
                print(f"✅ Configuração atualizada. Nova variação para outliers de temperatura: {self.var} °C e ID da simulação: {self.SimID}")
        

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
    temp_to_mqtt = tempToMqtt( topic, collection_name, outlier_collection_name)
    temp_to_mqtt.connectToMongoDB()
    temp_to_mqtt.sendingLoop()

if __name__ == "__main__":
    main()