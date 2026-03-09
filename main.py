import subprocess
import sys
import time


def main():
    """
    Script utilitário para iniciar a API (FastAPI) e a Interface (Streamlit) em simultâneo.
    Apenas para ambiente de desenvolvimento. Em produção, use contentores Docker separados.
    """
    print("A iniciar o servidor FastAPI (Backend)...")
    # Inicia a API na porta 8000
    api_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.api.routes:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]
    )

    # Dá 2 segundos para a API iniciar corretamente
    time.sleep(2)

    print("A iniciar a interface Streamlit (Frontend)...")
    # Inicia o Streamlit na porta 8501
    ui_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app/presentation/web_ui.py"]
    )

    try:
        # Mantém o script a correr
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("\nA encerrar os serviços...")
        api_process.terminate()
        ui_process.terminate()
        print("Serviços encerrados.")


if __name__ == "__main__":
    main()
