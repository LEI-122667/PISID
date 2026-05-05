"""
run_pc1.py - PC1 Launcher
Abre uma janela de terminal separada para cada script do PC1 (Mongo -> MQTT e Nuvem -> Mongo).

Scripts lancados:
  1. feedBack.py
  2. movesMongoToMqtt.py
  3. somToMqtt.py
  4. tempToMqtt.py
  5. somSimToMongo.py
  6. tempSimToMongo.py
  7. movesSimToMongo.py
"""

import subprocess
import os
import sys
import time

# ─── Configuração ────────────────────────────────────────────────────────────

# Pasta base: mesmo diretório onde este script está
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MONGO_MQTT_DIR = os.path.join(BASE_DIR, "mongoToMqtt")
NUVEM_MONGO_DIR = os.path.join(BASE_DIR, "nuvemToMongo")

# Python a usar (mesmo intérprete que está a correr este script)
PYTHON = sys.executable

# Scripts a lançar: (título da janela, caminho do script)
SCRIPTS = [
    ("PC1 - feedBack",           os.path.join(MONGO_MQTT_DIR, "feedBack.py")),
    ("PC1 - movesMongoToMqtt",   os.path.join(MONGO_MQTT_DIR, "movesMongoToMqtt.py")),
    ("PC1 - somToMqtt",          os.path.join(MONGO_MQTT_DIR, "somToMqtt.py")),
    ("PC1 - tempToMqtt",         os.path.join(MONGO_MQTT_DIR, "tempToMqtt.py")),
    ("PC1 - somSimToMongo",      os.path.join(NUVEM_MONGO_DIR, "somSimToMongo.py")),
    ("PC1 - tempSimToMongo",     os.path.join(NUVEM_MONGO_DIR, "tempSimToMongo.py")),
    ("PC1 - movesSimToMongo",    os.path.join(NUVEM_MONGO_DIR, "movesSimToMongo.py")),
]

# ─── Lançamento ──────────────────────────────────────────────────────────────

def launch_organized():
    print("=" * 60)
    print("  PC1 Launcher - Organizado")
    print("=" * 60)

    for i, (title, script) in enumerate(SCRIPTS):
        if not os.path.isfile(script):
            continue

        # --- Lógica de Posicionamento ---
        
        if "feedBack" in title:
            # Janela Grande à Esquerda
            # 80 colunas, 40 linhas, na posição (x=0, y=0)
            geom = "80x40+0+0"
        else:
            # Scripts à Direita (em grelha)
            # Calculamos a posição com base no índice (i-1 porque o feedback é o 0)
            idx = i - 1
            col = idx % 2      # Alterna entre coluna 0 e 1 à direita
            row = idx // 2     # Muda de linha a cada 2 scripts
            
            # Largura 60, Altura 12
            # X: começa depois da janela do feedback (aprox 700px)
            # Y: desce conforme a linha
            x_pos = 700 + (col * 550) 
            y_pos = row * 350
            geom = f"60x12+{x_pos}+{y_pos}"

        cmd = [
            "gnome-terminal", 
            f"--geometry={geom}", 
            "--title", title, 
            "--", "bash", "-c", f"python3 '{script}'; exec bash"
        ]

        subprocess.Popen(cmd, cwd=os.path.dirname(script))
        print(f"[OK] {title} posicionado em {geom}")
        time.sleep(0.3)

if __name__ == "__main__":
    launch_organized()
    input("\nPrime Enter para fechar...")
