import subprocess
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAZERUN_DIR = os.path.join(BASE_DIR, "mazerun")

class LauncherHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/launch" and "equipa" in params:
            equipa = params["equipa"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            launch_mazerun(equipa)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing equipa param")

    def log_message(self, format, *args):
        print(f"[Request] {args}")

def launch_mazerun(equipa):
    mazerun_exe = os.path.join(MAZERUN_DIR, "mazerun.exe")

    if not os.path.isfile(mazerun_exe):
        print(f"[ERRO] mazerun.exe nao encontrado: {mazerun_exe}")
        return

    mazerun_args = f'"{mazerun_exe}" {equipa} --flagMessage 1 --delay 1 --broker broker.hivemq.com --portbroker 1883'
    cmd_str = f'cmd /c "title MazeRun - Equipa {equipa} & {mazerun_args}"'

    print(f"[OK] A lancar mazerun para equipa {equipa}...")
    subprocess.Popen(
        cmd_str,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        cwd=MAZERUN_DIR
    )

if __name__ == "__main__":
    port = 9999
    print(f"[Launcher] A escutar em http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), LauncherHandler).serve_forever()