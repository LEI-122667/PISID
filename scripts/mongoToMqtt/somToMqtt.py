from setuptools import setup

from mongoToMqtt import mongoToMqtt

class somToMqtt(mongoToMqtt):
    def __init__(self, topic, collection_name, outlier_collection_name):
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
            self.var = self.setup_doc.get('outliers_som')
            print(f"✅ Configuração carregada. Variação para outliers de som: {self.var} DB e ID da simulação: {self.SimID}")

        if self.fetched:
            new_setup_doc = self.db["setup"].find_one()
            if new_setup_doc.get('IDSimulacao') != self.SimID:
                print("⚠️ Detetada mudança no ID da simulação. A recarregar configuração...")
                self.fetchInfoFromMongoDB()
                self.SimID = self.setup_doc.get('IDSimulacao')
                self.janela.clear()  # Limpa a janela para evitar comparações erradas com dados antigos
                self.var = self.setup_doc.get('outliers_som')
                print(f"✅ Configuração atualizada. Nova variação para outliers de som: {self.var} DB e ID da simulação: {self.SimID}")
        
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
    somToMqtt(topic, collection_name, outlier_collection_name)

if __name__ == "__main__":
    main()