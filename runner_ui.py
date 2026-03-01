import subprocess
import sys
import os

def launch_dashboard():
    # 1. Determina o caminho para o executável do Streamlit na tua .venv
    # No Windows, o caminho padrão é .venv/Scripts/streamlit.exe
    streamlit_exe = os.path.join(os.getcwd(), ".venv", "Scripts", "streamlit.exe")

    # 2. Caminho para o teu ficheiro de UI
    dashboard_script = os.path.join("ui", "dashboard.py")

    if not os.path.exists(streamlit_exe):
        print(f"❌ Erro: Streamlit não encontrado em {streamlit_exe}")
        print("Garante que a tua .venv está instalada corretamente.")
        return

    print(f"🚀 A iniciar o Studio-AI Dashboard...")

    # 3. Comando: streamlit run ui/dashboard.py
    cmd = [streamlit_exe, "run", dashboard_script]

    try:
        # Lança o processo e mantém a consola aberta para veres os logs
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard encerrado pelo utilizador.")
    except Exception as e:
        print(f"❌ Erro ao lançar o Dashboard: {e}")

if __name__ == "__main__":
    launch_dashboard()