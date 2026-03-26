"""Lança a API (uvicorn) e o frontend (streamlit) em paralelo."""

import signal
import subprocess
import sys


def main():
    api = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ],
    )
    frontend = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "frontend/app.py",
            "--server.port",
            "8501",
        ],
    )

    def _shutdown(sig, frame):
        print("\nEncerrando serviços...")
        api.terminate()
        frontend.terminate()
        api.wait()
        frontend.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print("API rodando em  http://localhost:8000")
    print("Streamlit em    http://localhost:8501")
    print("Pressione Ctrl+C para encerrar.\n")

    # Encerra tudo se qualquer processo morrer inesperadamente
    while True:
        if api.poll() is not None:
            print("API encerrou inesperadamente.")
            frontend.terminate()
            sys.exit(api.returncode)
        if frontend.poll() is not None:
            print("Streamlit encerrou inesperadamente.")
            api.terminate()
            sys.exit(frontend.returncode)
