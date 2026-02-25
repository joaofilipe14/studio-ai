import json
import os
import subprocess

def launch_manual_test():
    # Caminho onde o executável espera o ficheiro
    genome_path = os.path.join("projects", "game_001", "Builds", "game_genome.json")
    exe_path = os.path.join("projects", "game_001", "Builds", "Game001.exe")

    if not os.path.exists(genome_path):
        print(f"Erro: Genoma não encontrado em {genome_path}")
        return

    # 1. Carrega o genoma atual
    try:
        with open(genome_path, "r", encoding="utf-8") as f:
            genome = json.load(f)
    except Exception as e:
        print(f"Erro ao ler JSON: {e}")
        return

    genome["userControl"] = True

    # Garante que o modo existe no log
    current_mode = genome.get("mode", "PointToPoint")
    #current_mode = genome.get("mode", "Collect")

    # Garante que as regras existem antes de alterar o tempo
    if "rules" in genome:
        if genome["rules"].get("timeLimit", 0) < 10:
            genome["rules"]["timeLimit"] = 30.0

    # Grava de volta
    with open(genome_path, "w", encoding="utf-8") as f:
        json.dump(genome, f, indent=2)

    print(f"Modo Manual ATIVADO! Modo de jogo: {current_mode}")
    print(f"Executando: {exe_path}")

    # 3. Lança o jogo
    try:
        # No Windows, usamos shell=True ou passamos o caminho absoluto
        subprocess.run([os.path.abspath(exe_path)], check=True)
    except Exception as e:
        print(f"Erro ao lançar o executável: {e}")

if __name__ == "__main__":
    launch_manual_test()