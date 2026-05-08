from setuptools import setup

from mongoToMqtt import mongoToMqtt

class somToMqtt(mongoToMqtt):
    def __init__(self, topic, collection_name, outlier_collection_name):
        super().__init__(topic, collection_name, outlier_collection_name)
        self.var = None
        self.connectToMongoDB()
        self.sendingLoop()

    def isOutlier(self, doc):
        
        setup = list(self.db['setup'].find())
        self.var = setup[0].get('outliers_som') if setup else None
        print(f"Variação para outliers de som: {self.var} DB")
        
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