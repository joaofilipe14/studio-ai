import json
import os
import subprocess
import yaml
from rich import print

# Importamos a personalidade HUMANA e a função de PUBLISH
from brain.game_director import evolve_human_genome
from db.evolution_logger import init_db, log_evolution_to_db
from scripts.publish import publish_game # <--- NOVO IMPORT AQUI

def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def launch_manual_test():
    config = load_yaml("config.yaml")
    db_path = os.path.join(config["paths"]["logs"], "evolution.db")
    init_db(db_path)

    release_dir = os.path.join("releases", "game_prod")
    genome_path = os.path.join(release_dir, "game_genome.json")
    exe_path = os.path.join(release_dir, "Game001.exe")
    metrics_path = os.path.join(release_dir, "metrics.json")

    # ---> A NOVA LÓGICA DE AUTO-PUBLISH <---
    if not os.path.exists(exe_path) or not os.path.exists(genome_path):
        print(f"[yellow]Aviso: Jogo de produção não encontrado em {release_dir}.[/yellow]")
        print("[cyan]A iniciar a montagem da Release de Produção automaticamente...[/cyan]")
        publish_game() # Chamamos o teu script de publish!

        # Verificamos de novo se a compilação foi bem sucedida
        if not os.path.exists(exe_path) or not os.path.exists(genome_path):
            print("[red]Erro crítico: Falha ao criar a Release. O Orquestrador já fez a primeira build na pasta projects?[/red]")
            return

    # 2. Carrega o genoma
    try:
        with open(genome_path, "r", encoding="utf-8") as f:
            full_genome_data = json.load(f)
    except Exception as e:
        print(f"[red]Erro ao ler JSON: {e}[/red]")
        return

    # Escolhe o primeiro modo
    target_mode = "PointToPoint"
    current_genome = None
    genome_index = 0

    if "configs" in full_genome_data:
        for i, c in enumerate(full_genome_data["configs"]):
            if c.get("mode") == target_mode:
                current_genome = c
                genome_index = i
                break

        if current_genome is None and len(full_genome_data["configs"]) > 0:
            current_genome = full_genome_data["configs"][0]
            genome_index = 0
            target_mode = current_genome.get("mode")

    if current_genome is None:
        print("[red]Erro: Modo não encontrado no Genoma.[/red]")
        return

    # Garante que as regras estão justas para um Humano começar (e escreve na RAIZ)
    full_genome_data["userControl"] = True
    if "rules" in current_genome and current_genome["rules"].get("timeLimit", 0) < 10:
        current_genome["rules"]["timeLimit"] = 30.0

    print(f"\n[bold cyan]🎮 Modo Manual ATIVADO! Modo: {target_mode}[/bold cyan]")
    print("[white]A abrir o jogo de Produção... A IA vai avaliar a tua performance no final.[/white]")

    # 3. Lança o jogo (Sem o check=True e com o cwd correto)
    try:
        exe_dir = os.path.dirname(os.path.abspath(exe_path))
        subprocess.run([os.path.abspath(exe_path)], cwd=exe_dir)
    except Exception as e:
        print(f"[red]Erro ao lançar o executável: {e}[/red]")
        return

    # 4. Lê a telemetria pós-jogo
    print("\n[cyan]Jogo terminado. A ler telemetria da tua sessão...[/cyan]")
    if not os.path.exists(metrics_path):
        print("[yellow]Aviso: metrics.json não gerado pelo jogo. Nenhuma evolução aplicada.[/yellow]")
        return

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics_data = json.load(f)

    print(f"[white]Métricas recebidas: Win Rate = {metrics_data.get('win_rate', 0.0)}[/white]")

    # 5. Chama o Game Director para avaliar o Humano
    print("[cyan]A pedir ao Diretor de IA para balancear o jogo para ti...[/cyan]")
    evolved_data = evolve_human_genome(config, metrics_data, current_genome)

    if evolved_data and "new_genome" in evolved_data:
        new_genome = evolved_data["new_genome"]
        full_genome_data["configs"][genome_index] = new_genome
        full_genome_data["userControl"] = True # Garante que ficas com o controlo

        # Guarda na pasta de Produção
        with open(genome_path, "w", encoding="utf-8") as f:
            json.dump(full_genome_data, f, indent=2)

        report_text = evolved_data.get("report", "No report text provided.")
        log_evolution_to_db(db_path, metrics_data, new_genome, report_text)

        print(f"[bold green]✅ Genoma evoluído gravado! O teu jogo foi ajustado.[/bold green]")
    else:
        print("[red]Falha ao evoluir genoma. Tenta novamente.[/red]")

if __name__ == "__main__":
    launch_manual_test()