import os
import shutil
import yaml
import json
from rich import print

def load_yaml(path: str):
    """Carrega as configurações do projeto de forma absoluta."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def publish_game():
    print("[cyan]A iniciar o Pipeline de Release (Studio-AI - Fase 4)...[/cyan]")

    # 🚨 NOVO: Descobre a raiz do projeto de forma absoluta!
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(script_dir, ".."))

    # 0. CARREGAR CONFIGURAÇÃO DINÂMICA
    config_path = os.path.join(base_dir, "config.yaml")
    config = load_yaml(config_path)
    paths = config.get("paths", {})

    # Lemos os caminhos configurados e juntamos à base do projeto
    projects_root = os.path.join(base_dir, paths.get("projects", "workspace/projects"))
    releases_root = os.path.join(base_dir, paths.get("releases", "workspace/releases"))
    hall_of_fame_dir = os.path.join(base_dir, paths.get("hall_of_fame", "workspace/hall_of_fame"))

    pn = "game_001"
    builds_dir = os.path.join(projects_root, pn, "Builds")
    release_dir = os.path.join(releases_root, "game_prod")

    if not os.path.exists(builds_dir):
        print(f"[red]Erro: Pasta de Builds não encontrada em {builds_dir}.[/red]")
        print("[yellow]Dica: Já correnteste o orchestrator para compilar o jogo?[/yellow]")
        return

    print(f"[white]A limpar a versão de produção anterior em {release_dir}...[/white]")
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir, exist_ok=True)

    print(f"[white]A empacotar o executável e dados para a Produção...[/white]")

    # 1. Copiar todos os ficheiros compilados do Unity (incluindo o .exe)
    for item in os.listdir(builds_dir):
        s = os.path.join(builds_dir, item)
        d = os.path.join(release_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # 2. Garantir que os ficheiros JSON estruturais vão junto com a nova prioridade
    json_files = ["level_genome.json", "roster.json", "safe_room_items.json"]
    for j_file in json_files:
        sources = []

        # 🎯 Lógica Inteligente para o Hall of Fame
        if j_file == "level_genome.json" and os.path.exists(hall_of_fame_dir):
            # Procura a campanha de sucesso mais recente
            masterpieces = [f for f in os.listdir(hall_of_fame_dir) if f.startswith("campaign_masterpiece_") and f.endswith(".json")]
            if masterpieces:
                masterpieces.sort(reverse=True) # Põe a mais recente no topo (baseado na data do ficheiro)
                sources.append(os.path.join(hall_of_fame_dir, masterpieces[0]))

        # Constrói a lista de prioridades (do mais importante para o menos importante)
        sources.extend([
            os.path.join(hall_of_fame_dir, j_file),     # 1.5. Hall of Fame (caso tenha o nome exato)
            os.path.join(builds_dir, j_file),           # 2. Pasta de Builds (A Campanha a ser ativamente evoluída)
            os.path.join(base_dir, "templates", "json", j_file),  # 3. Templates (Onde guardamos as evoluções manuais)
            os.path.join(base_dir, j_file),             # 4. Raiz do projeto
            os.path.join(base_dir, "templates", "unity", j_file)  # 5. Template original de fallback
        ])

        copied = False
        for src in sources:
            if os.path.exists(src):
                dest = os.path.join(release_dir, j_file)
                shutil.copy2(src, dest)
                print(f"[green]✓ {j_file} empacotado (via {src}).[/green]")
                copied = True
                break

        if not copied:
            print(f"[yellow]Aviso: Não encontrei o {j_file} em nenhum diretório de origem.[/yellow]")

    clean_save = {
        "playerName": "Player",
        "currentCampaignLevel": 1,
        "wallet": {
            "totalCoins": 0,
            "timeCrystals": 0
        },
        "loadout": {
            "selectedClassID": "Explorer"
        },
        "unlockedClasses": [
            "Explorer"
        ],
        "purchasedUpgrades": {
            "startExtraTimeLvl": 0,
            "morePowerUpsLvl": 0,
            "permSpeedLvl": 0,
            "trapReductionLvl": 0
        },
        "purchasedItems": [],
        "stats": {
            "totalTrapsHit": 0,
            "totalWins": 0,
            "currentLives": 3,
            "maxLives": 3,
            "basePowerUpCount": 3
        }
    }

    clean_save_path = os.path.join(release_dir, "player_save.json")
    with open(clean_save_path, "w", encoding="utf-8") as f:
        json.dump(clean_save, f, indent=4)
    print(f"\n[bold green]🎉 Release de Produção concluída com sucesso![/bold green]")
    print(f"O teu jogo final está na pasta: {os.path.abspath(release_dir)}\n")

if __name__ == "__main__":
    publish_game()