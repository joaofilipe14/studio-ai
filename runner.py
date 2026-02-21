import yaml
import time
import sys
import json
import os
from brain.orchestrator import main as run_orchestrator

def set_genome_mode(mode_name):
    """Força a alteração do modo no ficheiro game_genome.json antes da execução."""
    # O caminho deve ser o mesmo que o orchestrator usa
    genome_path = os.path.join("projects", "game_001", "game_genome.json")

    if os.path.exists(genome_path):
        with open(genome_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["mode"] = mode_name

        with open(genome_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[RUNNER] Modo forçado para: {mode_name}")

def main_runner():
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        print(f"[ERRO] Falha ao ler o config.yaml: {e}")
        sys.exit(1)

    # Definimos 5 para cada, ou usamos o dobro do num_runs do config
    runs_per_mode = config.get('num_runs', 5)
    modes = config.get('run', {}).get('modes', ["PointToPoint"])

    print("=" * 50)
    print(f" INICIANDO RUNNER BIFÁSICO: {runs_per_mode} de PointToPoint + {runs_per_mode} de Collect ")
    print("=" * 50 + "\n")

    for mode in modes:
        print(f"\n[FASE: MODO {mode.upper()}]")
        for i in range(1, runs_per_mode + 1):
            print(f"\n>>> GERAÇÃO {i}/5 ({mode}) <<<")

            # 1. Forçamos o modo antes de o Orchestrator correr
            set_genome_mode(mode)

            try:
                # 2. O Orchestrator corre, simula e deixa a IA evoluir os parâmetros
                # (A IA vai manter o modo que injetámos se o prompt for respeitado)
                run_orchestrator()
            except Exception as e:
                print(f"\n[ERRO CRÍTICO] Falha na geração: {e}")

            time.sleep(3)

    print("\n" + "=" * 50)
    print(" CICLO COMPLETO: 10 GERAÇÕES (5 P2P + 5 COLLECT) CONCLUÍDAS! ")
    print("=" * 50)

if __name__ == "__main__":
    main_runner()