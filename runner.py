import yaml
import time
import sys
import json
import os
from brain.orchestrator import main as run_orchestrator
from brain.plan_master import create_master_plan

def set_genome_mode(mode_name):
    """Força a alteração do modo no ficheiro game_genome.json na pasta de Builds."""
    # Nota: O caminho deve apontar para onde o jogo realmente lê o genoma (Builds)
    genome_path = os.path.join("projects", "game_001", "Builds", "game_genome.json")

    if os.path.exists(genome_path):
        with open(genome_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["mode"] = mode_name

        with open(genome_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[RUNNER] Modo forçado para: {mode_name}")
    else:
        print(f"[AVISO] Ficheiro de genoma não encontrado para forçar modo: {genome_path}")

def main_runner():
    # 1. Carregar Configuração
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        print(f"[ERRO] Falha ao ler o config.yaml: {e}")
        sys.exit(1)

    # 3. Ler parâmetros de execução do YAML
    run_section = config.get('run', {})
    runs_per_mode = run_section.get('num_runs', 2)
    modes = run_section.get('modes', ["PointToPoint"])

    total_previsto = runs_per_mode * len(modes)

    print("=" * 60)
    print(f" RUNNER BIFÁSICO INICIADO")
    print(f" Configuração: {runs_per_mode} runs por cada um dos {len(modes)} modos")
    print(f" Total de gerações: {total_previsto}")
    print("=" * 60 + "\n")

    for mode in modes:
        print(f"\n[ENTRANDO NA FASE: {mode.upper()}]")
        for i in range(1, runs_per_mode + 1):
            print(f"\n>>> GERAÇÃO {i}/{runs_per_mode} ({mode}) <<<")

            # A) Forçamos o modo no genoma da Build atual
            set_genome_mode(mode)

            try:
                # B) O Orquestrador executa o Master Plan e a Evolução
                run_orchestrator()
            except Exception as e:
                print(f"\n[ERRO NA GERAÇÃO] Falha na execução: {e}")

            # Pequena pausa para o sistema respirar e fechar ficheiros
            time.sleep(2)

    print("\n" + "=" * 60)
    print(f" CICLO COMPLETO CONCLUÍDO: {total_previsto} GERAÇÕES PROCESSADAS")
    print("=" * 60)

if __name__ == "__main__":
    main_runner()