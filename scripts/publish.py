import os
import shutil
import json
import glob
from rich import print

# 1. Descobrir a Raiz do Projeto dinamicamente (para funcionar em qualquer pasta)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # C:\studio-ai\scripts
ROOT_DIR = os.path.dirname(SCRIPT_DIR)                  # C:\studio-ai

def find_best_genome(hof_dir: str) -> str:
    """Procura no Hall of Fame o genoma com o Win Rate mais próximo de 0.75."""
    files = glob.glob(os.path.join(hof_dir, "*.json"))
    if not files:
        return None

    best_file = None
    min_diff = float('inf')
    target_wr = 0.75

    for f in files:
        try:
            basename = os.path.basename(f).replace(".json", "")
            parts = basename.split("_")
            wr = float(parts[-1])

            diff = abs(wr - target_wr)
            if diff < min_diff:
                min_diff = diff
                best_file = f
        except Exception:
            continue

    if not best_file:
        best_file = max(files, key=os.path.getctime)

    return best_file

def publish_game():
    print("[cyan]A iniciar o Pipeline de Release (Studio-AI)...[/cyan]")

    # 2. Definir Caminhos apontando para a Raiz (ROOT_DIR)
    source_build_dir = os.path.join(ROOT_DIR, "projects", "game_001", "Builds")
    release_dir = os.path.join(ROOT_DIR, "releases", "game_prod")
    hof_dir = os.path.join(ROOT_DIR, "hall_of_fame")

    if not os.path.exists(source_build_dir):
        print(f"[red]Erro: Pasta de compilação não encontrada em {source_build_dir}. Corre o orchestrator.py primeiro.[/red]")
        return

    if os.path.exists(release_dir):
        print("[yellow]A limpar a versão de produção anterior...[/yellow]")
        shutil.rmtree(release_dir)

    print(f"[cyan]A empacotar o executável para {release_dir}...[/cyan]")
    shutil.copytree(source_build_dir, release_dir)

    print("[cyan]A analisar o Hall of Fame...[/cyan]")
    best_genome_path = find_best_genome(hof_dir)

    target_genome_path = os.path.join(release_dir, "game_genome.json")

    if best_genome_path:
        print(f"[green]Melhor genoma encontrado: {os.path.basename(best_genome_path)}[/green]")

        with open(best_genome_path, "r", encoding="utf-8") as f:
            best_genome_data = json.load(f)
        best_genome_data["userControl"] = True

        if "configs" in best_genome_data:
            for config in best_genome_data["configs"]:
                if "rules" in config and config["rules"].get("timeLimit", 0) < 20:
                    config["rules"]["timeLimit"] += 15.0

        with open(target_genome_path, "w", encoding="utf-8") as f:
            json.dump(best_genome_data, f, indent=2)

        print("[green]Genoma injetado com controlos humanos ativados![/green]")
    else:
        print("[yellow]Aviso: Nenhum genoma encontrado no Hall of Fame. A usar o genoma de desenvolvimento padrão.[/yellow]")
        if os.path.exists(target_genome_path):
            with open(target_genome_path, "r", encoding="utf-8") as f:
                fallback_data = json.load(f)

            # ---> COLOCAR NA RAIZ (Nova arquitetura!) <---
            fallback_data["userControl"] = True

            # (Opcional) Dar a abébia do tempo também no fallback
            if "configs" in fallback_data:
                for config in fallback_data["configs"]:
                    if "rules" in config and config["rules"].get("timeLimit", 0) < 20:
                        config["rules"]["timeLimit"] += 15.0

            with open(target_genome_path, "w", encoding="utf-8") as f:
                json.dump(fallback_data, f, indent=2)

    metrics_cleanup = os.path.join(release_dir, "metrics.json")
    if os.path.exists(metrics_cleanup):
        os.remove(metrics_cleanup)

    print("\n[bold green]🎉 Release de Produção concluída com sucesso![/bold green]")
    print(f"O teu jogo final, balanceado pela IA e pronto a jogar, está na pasta: [bold white]{release_dir}[/bold white]")
