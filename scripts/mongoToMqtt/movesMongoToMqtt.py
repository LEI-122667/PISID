from mongoToMqtt import mongoToMqtt

class movesToMqtt(mongoToMqtt):
    def __init__(self, topic, collection_name, outlier_collection_name):
        super().__init__(topic, collection_name, outlier_collection_name)
        self.corredores_col = None
        self.n_marsamis_global = None

    def fetchInfoFromMongoDB(self):
        self.corredores_col = self.db["corredores"]
        setup_collection = self.db["setup"]
        setup_doc = setup_collection.find_one()
        
        if setup_doc:
            self.n_marsamis_global = setup_doc.get('numbermarsamis')
            print(f"✅ [FETCH] Setup carregado: Total de Marsamis = {self.n_marsamis_global}")
        else:
            print("⚠️ [FETCH] Aviso: Documento de setup não encontrado.")

    def isOutlier(self, doc):
        # 1. Capture and Debug Input Data
        roomOriginal = doc.get('RoomOrigin')
        roomDestino = doc.get('RoomDestiny')
        numMarsami = doc.get('Marsami')
        nMarsami_limit = doc.get('numbermarsamis') or self.n_marsamis_global


        print(f"\n🔍 [DEBUG] Verificando Doc ID: {doc.get('idIncremental')}")
        print(f"   -> Trajeto: {roomOriginal} (type: {type(roomOriginal)}) -> {roomDestino} (type: {type(roomDestino)})")
        print(f"   -> Marsami: {numMarsami} | Limite: {nMarsami_limit}")

        # 2. Logic Check: Same Room
        if roomOriginal == roomDestino:
            self.motivo_outlier = f"RoomOriginal e RoomDestino são iguais ({roomOriginal})"
            print(f"   ❌ OUTLIER: {self.motivo_outlier}")
            return True

        # 3. Database Check: Corridor Existence
        # Note: If DB stores as Int but doc has String, we must cast: int(roomOriginal)
        query = {"origin": roomOriginal, "destination": roomDestino}
        
        if roomOriginal == 0:
            corredor = True # Automatically allow moves from the "lobby"
        else:
            corredor = self.corredores_col.find_one(query)
        
        print(f"   -> Verificando corredor no DB com query: {corredor}")

        if not corredor:
            self.motivo_outlier = f"Corredor não existe no mapa: {roomOriginal} -> {roomDestino}"
            print(f"   ❌ OUTLIER: {self.motivo_outlier} (Query: {query})")
            return True
        
        print(f"   ✅ Corredor validado no mapa.")

        # 4. Marsami Validation
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
    
    bridge = movesToMqtt(topic, collection_name, outlier_collection_name)
    bridge.connectToMongoDB()
    bridge.fetchInfoFromMongoDB()
    bridge.sendingLoop()

if __name__ == "__main__":
    main()