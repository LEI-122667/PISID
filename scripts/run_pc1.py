"""
run_pc1.py - PC1 Launcher
Abre uma janela de terminal separada para cada script do PC1 (Mongo -> MQTT).

Scripts lancados:
  1. feedBack.py
  2. mongoToMqtt.py
  3. movesMongoToMqtt.py
  4. somToMqtt.py
  5. tempToMqtt.py
"""

import subprocess
import os
import sys
import time

# ─── Configuração ────────────────────────────────────────────────────────────

# Pasta base: mesmo diretório onde este script está
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MONGO_MQTT_DIR = os.path.join(BASE_DIR, "mongoToMqtt")

# Python a usar (mesmo intérprete que está a correr este script)
PYTHON = sys.executable

# Scripts a lançar: (título da janela, caminho do script)
SCRIPTS = [
    ("PC1 - feedBack",           os.path.join(MONGO_MQTT_DIR, "feedBack.py")),
    ("PC1 - mongoToMqtt",        os.path.join(MONGO_MQTT_DIR, "mongoToMqtt.py")),
    ("PC1 - movesMongoToMqtt",   os.path.join(MONGO_MQTT_DIR, "movesMongoToMqtt.py")),
    ("PC1 - somToMqtt",          os.path.join(MONGO_MQTT_DIR, "somToMqtt.py")),
    ("PC1 - tempToMqtt",         os.path.join(MONGO_MQTT_DIR, "tempToMqtt.py")),
]

# ─── Lançamento ──────────────────────────────────────────────────────────────

def launch(title: str, script: str):
    """Abre uma nova janela cmd com o titulo dado e corre o script Python."""
    if not os.path.isfile(script):
        print(f"[AVISO] Script nao encontrado, a saltar: {script}")
        return

    # Usa CREATE_NEW_CONSOLE para abrir uma janela separada sem depender
    # do comando 'start', que tem problemas com caminhos com espacos.
    # 'title TITULO & python script.py' define o titulo e corre o script.
    # Passar como string evita problemas de "double-quoting" internos do Python no Windows.
    cmd_str = f'cmd /k "title {title} & "{PYTHON}" "{script}""'
    subprocess.Popen(
        cmd_str,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        cwd=os.path.dirname(script),
    )
    print(f"[OK] Lancado: {title}")
    time.sleep(0.5)  # pequena pausa para nao sobrepor janelas


if __name__ == "__main__":
    print("=" * 60)
    print("  PC1 Launcher - Mongo -> MQTT")
    print("=" * 60)
    for title, script in SCRIPTS:
        launch(title, script)
    print("\nTodos os scripts PC1 foram lançados.")
    input("\nPrime Enter para fechar este launcher...\n")
