from mongoToMqtt import mongoToMqtt

class movesToMqtt(mongoToMqtt):
    def __init__(self, topic, collection_name, outlier_collection_name):
        super().__init__(topic, collection_name, outlier_collection_name)
        self.corredores_col = None
        self.n_marsamis_global = None
        self.connectToMongoDB()
        self.sendingLoop()

    def isOutlier(self, doc):
        if not self.fetched:
            print("⚠️ Aviso: Dados de configuração a carregados...")
            self.fetchInfoFromMongoDB()
            self.SimID = self.setup_doc.get('IDSimulacao')
            self.n_marsamis_global = self.setup_doc.get('numbermarsamis')
            self.fetched = True

        if self.fetched:
            new_setup_doc = self.db["setup"].find_one()
            if new_setup_doc.get('IDSimulacao') != self.SimID:
                print("⚠️ Detetada mudança no ID da simulação. A recarregar configuração...")
                self.fetchInfoFromMongoDB()
                self.SimID = self.setup_doc.get('IDSimulacao')
                self.n_marsamis_global = self.setup_doc.get('numbermarsamis')

        roomOriginal = doc.get('RoomOrigin')
        roomDestino = doc.get('RoomDestiny')
        numMarsami = doc.get('Marsami')
        nMarsami_limit = doc.get('numbermarsamis') or self.n_marsamis_global


        print(f"\n🔍 [DEBUG] Verificando Doc ID: {doc.get('idIncremental')}")
        print(f"   -> Trajeto: {roomOriginal} (type: {type(roomOriginal)}) -> {roomDestino} (type: {type(roomDestino)})")
        print(f"   -> Marsami: {numMarsami} | Limite: {nMarsami_limit}")


        if roomOriginal != 0 and roomDestino != 0 and roomOriginal == roomDestino:
            self.motivo_outlier = f"RoomOriginal e RoomDestino são iguais ({roomOriginal})"
            print(f"   ❌ OUTLIER: {self.motivo_outlier}")
            return True

        query = {"origin": roomOriginal, "destination": roomDestino}
        
        if roomOriginal == 0:
            corredor = True
        else:
            corredor = self.corredores_col.find_one(query)
        
        print(f"   -> Verificando corredor no DB com query: {corredor}")

        if not corredor:
            self.motivo_outlier = f"Corredor não existe no mapa: {roomOriginal} -> {roomDestino}"
            print(f"   ❌ OUTLIER: {self.motivo_outlier} (Query: {query})")
            return True
        
        print(f"   ✅ Corredor validado no mapa.")

        if numMarsami is None or numMarsami < 1 or (nMarsami_limit and numMarsami > nMarsami_limit):
            self.motivo_outlier = f"Número de Marsami ({numMarsami}) inválido (Limite: {nMarsami_limit})"
            print(f"   ❌ OUTLIER: {self.motivo_outlier}")
            return True
        
        print(f"   ✅ Movimento totalmente validado.")
        return False

def main():
    topic = "pisid_2_moves"
    collection_name = "sensor_movimento"
    outlier_collection_name = "outliers_DadosErrados_movimentos"
    
    movesToMqtt(topic, collection_name, outlier_collection_name)

if __name__ == "__main__":
    main()