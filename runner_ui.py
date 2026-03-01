import subprocess
import sys
import os

def launch_dashboard():
    # Usamos o Python ativo da .venv em vez do streamlit.exe
    python_exe = sys.executable
    dashboard_script = os.path.join("ui", "dashboard.py")

    if not os.path.exists(dashboard_script):
        print(f"❌ Erro: Ficheiro não encontrado em {dashboard_script}")
        return

    print(f"🚀 A iniciar o Studio-AI Dashboard...")

    # O truque mágico: chamar o módulo com "python -m streamlit run ..."
    cmd = [python_exe, "-m", "streamlit", "run", dashboard_script]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard encerrado pelo utilizador.")
    except Exception as e:
        print(f"❌ Erro ao lançar o Dashboard: {e}")

if __name__ == "__main__":
    launch_dashboard()