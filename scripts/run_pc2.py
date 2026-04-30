"""
run_pc2.py - PC2 Launcher
Abre uma janela de terminal separada para cada script do PC2 (MQTT -> MySQL + Agente).

Scripts lancados:
  1. movimentoMqqtToMySql.py
  2. somMqqtToMySql.py
  3. temperaturaMqqtToMySql.py
  4. agentejogo.py
"""

import subprocess
import os
import sys
import time

# ─── Configuração ────────────────────────────────────────────────────────────

# Pasta base: mesmo diretório onde este script está
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MQTT_MYSQL_DIR = os.path.join(BASE_DIR, "mqttToMySql")

# Python a usar (mesmo intérprete que está a correr este script)
PYTHON = sys.executable

# Scripts a lançar: (título da janela, caminho do script)
SCRIPTS = [
    ("PC2 - movimentoMqttToMySql",   os.path.join(MQTT_MYSQL_DIR, "movimentoMqqtToMySql.py")),
    ("PC2 - somMqttToMySql",         os.path.join(MQTT_MYSQL_DIR, "somMqqtToMySql.py")),
    ("PC2 - temperaturaMqttToMySql", os.path.join(MQTT_MYSQL_DIR, "temperaturaMqqtToMySql.py")),
    ("PC2 - agentejogo",             os.path.join(BASE_DIR, "agentejogo.py")),
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
    print("  PC2 Launcher - MQTT -> MySQL + Agente")
    print("=" * 60)
    for title, script in SCRIPTS:
        launch(title, script)
    print("\nTodos os scripts PC2 foram lançados.")
    input("\nPrime Enter para fechar este launcher...\n")
