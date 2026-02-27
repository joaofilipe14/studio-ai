import yaml
import time
import sys
import json
import os
from rich import print

# Agora importamos o main limpo do orchestrator
from scripts.orchestrator import main as run_orchestrator

def set_genome_mode(mode_name):
    """Força a alteração do modo ativo no ficheiro game_genome.json."""
    genome_path = os.path.join("projects", "game_001", "Builds", "game_genome.json")

    if os.path.exists(genome_path):
        with open(genome_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Atualizamos a flag root que diz ao Unity qual config do Array deve jogar
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

    # 2. Ler parâmetros de execução do YAML
    run_section = config.get('run', {})
    runs_per_mode = run_section.get('num_runs', 2)
    modes = run_section.get('modes', ["PointToPoint", "Collect"]) # Adicionei o Collect aqui!

    total_previsto = runs_per_mode * len(modes)

    print("=" * 60)
    print(f" RUNNER BIFÁSICO INICIADO")
    print(f" Configuração: {runs_per_mode} runs por cada um dos {len(modes)} modos")
    print(f" Total de gerações: {total_previsto}")
    print("=" * 60 + "\n")

    for mode in modes:
        print(f"\n[bold yellow][ENTRANDO NA FASE: {mode.upper()}][/bold yellow]")
        for i in range(1, runs_per_mode + 1):
            print(f"\n>>> GERAÇÃO {i}/{runs_per_mode} ({mode}) <<<")

            # A) Forçamos o modo no genoma da Build atual
            set_genome_mode(mode)

            try:
                # B) O Orquestrador executa a Simulação e a Evolução
                run_orchestrator()
            except Exception as e:
                erro_msg = str(e)
                print(f"\n[bold red][ERRO NA GERAÇÃO] Falha na execução:[/bold red] {erro_msg}")

                # Se o erro for de conexão ao Ollama (porta 11434 recusada / WinError 10061)
                if "10061" in erro_msg or "Max retries exceeded" in erro_msg or "ConnectionRefused" in erro_msg:
                    print("\n[bold red]🚨 ALERTA CRÍTICO: O servidor Ollama está desligado![/bold red]")
                    print("[yellow]Por favor, liga o Ollama (abre a aplicação ou corre 'ollama serve' no terminal).[/yellow]")
                    print("[red]A interromper o Runner para não desperdiçar gerações...[/red]")
                    sys.exit(1) # <--- ISTO MATA O RUNNER IMEDIATAMENTE
                else:
                    print("\n[bold red]🚨 Erro fatal desconhecido. A interromper o Runner por segurança.[/bold red]")
                    sys.exit(1)

            # Pequena pausa para o sistema respirar e fechar ficheiros (SQLite, JSONs)
            time.sleep(2)

    print("\n" + "=" * 60)
    print(f" 🎉 CICLO COMPLETO CONCLUÍDO: {total_previsto} GERAÇÕES PROCESSADAS")
    print("=" * 60)

if __name__ == "__main__":
    main_runner()