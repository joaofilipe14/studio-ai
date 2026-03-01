import yaml
import time
import sys
import json
import os
from rich import print

# Importamos o main limpo do orchestrator
from scripts.orchestrator import main as run_orchestrator

def set_level_mode(mode_name):
    """Força a alteração do modo ativo no ficheiro level_genome.json."""
    # Atualizamos tanto na raiz (para o Ollama ler) como na Build (para o Unity jogar)
    root_path = "level_genome.json"
    build_path = os.path.join("projects", "game_001", "Builds", "level_genome.json")

    paths_to_update = [root_path, build_path]
    updated = False

    for path in paths_to_update:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Atualiza diretamente o modo na raiz do level_genome
                data["mode"] = mode_name

                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                print(f"[RUNNER] Modo forçado para: {mode_name} em {path}")
                updated = True
            except Exception as e:
                print(f"[ERRO] Falha ao modificar {path}: {e}")
        else:
            print(f"[AVISO] Ficheiro não encontrado: {path}")

    if not updated:
        print(f"[AVISO CRÍTICO] O Runner não conseguiu forçar o modo '{mode_name}'. Verifica se os ficheiros JSON existem.")

def main_runner():
    # 1. Carregar Configuração
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        print(f"[ERRO] Falha ao ler o config.yaml: {e}")
        sys.exit(1)

    # 2. Ler parâmetros de execução do YAML
    run_section = config.get('run', {})
    runs_per_mode = run_section.get('num_runs', 2)
    modes = run_section.get('modes', ["PointToPoint", "Collect"])

    total_previsto = runs_per_mode * len(modes)

    print("=" * 60)
    print(f" RUNNER BIFÁSICO INICIADO (NOVA ARQUITETURA)")
    print(f" Configuração: {runs_per_mode} runs por cada um dos {len(modes)} modos")
    print(f" Total de gerações: {total_previsto}")
    print("=" * 60 + "\n")

    for mode in modes:
        print(f"\n[bold yellow][ENTRANDO NA FASE: {mode.upper()}][/bold yellow]")
        for i in range(1, runs_per_mode + 1):
            print(f"\n>>> GERAÇÃO {i}/{runs_per_mode} ({mode}) <<<")

            # A) Forçamos o modo no novo genoma de nível (Level Genome)
            set_level_mode(mode)

            try:
                # B) O Orquestrador executa a Simulação e a Evolução
                run_orchestrator()
            except Exception as e:
                erro_msg = str(e)
                print(f"\n[bold red][ERRO NA GERAÇÃO] Falha na execução:[/bold red] {erro_msg}")

                # Proteção contra falhas do Ollama
                if "10061" in erro_msg or "Max retries exceeded" in erro_msg or "ConnectionRefused" in erro_msg:
                    print("\n[bold red]🚨 ALERTA CRÍTICO: O servidor Ollama está desligado![/bold red]")
                    print("[yellow]Por favor, liga o Ollama (abre a aplicação ou corre 'ollama serve' no terminal).[/yellow]")
                    print("[red]A interromper o Runner para não desperdiçar gerações...[/red]")
                    sys.exit(1)
                else:
                    print("\n[bold red]🚨 Erro fatal desconhecido. A interromper o Runner por segurança.[/bold red]")
                    sys.exit(1)

            # Pausa para o sistema respirar
            time.sleep(2)

    print("\n" + "=" * 60)
    print(f" 🎉 CICLO COMPLETO CONCLUÍDO: {total_previsto} GERAÇÕES PROCESSADAS")
    print("=" * 60)

if __name__ == "__main__":
    main_runner()