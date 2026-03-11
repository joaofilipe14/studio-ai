import json
import os
import subprocess
import yaml
from rich import print

from services.game_director.logic import evolve_human_genome
from shared.db.evolution_logger import init_db, log_evolution_to_db
from scripts.publish import publish_game

def load_yaml(path: str):
    """Carrega as configurações do projeto."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuração não encontrada em {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def launch_manual_game():
    # 0. CARREGAR CONFIGURAÇÃO
    config = load_yaml("config.yaml")

    # Extrair caminhos do YAML com valores padrão de segurança
    paths = config.get("paths", {})
    logs_dir = paths.get("data", "workspace/data")
    projects_dir = paths.get("projects", "workspace/projects")

    db_path = os.path.join(logs_dir, "evolution.db")
    init_db(db_path)

    # Definimos a pasta de produção dentro da estrutura de workspace
    releases_root = paths.get("releases", "workspace/releases")
    release_dir = os.path.join(releases_root, "game_prod")

    # 1. CAMINHOS DE PRODUÇÃO
    level_path = os.path.join(release_dir, "level_genome.json")
    save_path = os.path.join(release_dir, "player_save.json")
    exe_path = os.path.join(release_dir, "Game001.exe")
    metrics_path = os.path.join(release_dir, "metrics.json")

    # 2. LÓGICA DE AUTO-PUBLISH
    if not os.path.exists(exe_path) or not os.path.exists(level_path):
        print(f"[yellow]Aviso: Jogo de produção não encontrado em {release_dir}.[/yellow]")
        print("[cyan]A iniciar a montagem da Release de Produção automaticamente...[/cyan]")
        publish_game()

        if not os.path.exists(exe_path) or not os.path.exists(level_path):
            print("[red]Erro crítico: Falha ao criar a Release. Garante que o Orquestrador já criou o projeto.[/red]")
            return

    # 3. CARREGA A CAMPANHA (Array JSON)
    try:
        with open(level_path, "r", encoding="utf-8") as f:
            campaign = json.load(f)
        if isinstance(campaign, dict):
            campaign = [campaign]
    except Exception as e:
        print(f"[red]Erro ao ler o level_genome.json: {e}[/red]")
        return

    # 4. CARREGA O SAVE DO JOGADOR
    player_name = "Humano"
    current_campaign_level = 1
    if os.path.exists(save_path):
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
                player_name = save_data.get("playerName", "Humano")
                current_campaign_level = save_data.get("currentCampaignLevel", 1)
        except Exception:
            pass

    print(f"\n[bold cyan]🎮 Modo Manual ATIVADO, {player_name}![/bold cyan]")
    print(f"[white]Estás no Nível {current_campaign_level} da Campanha.[/white]")
    print("[white]A abrir o jogo... A IA vai analisar a tua performance.[/white]")

    if os.path.exists(metrics_path):
        os.remove(metrics_path)

    # 5. LANÇA O JOGO
    try:
        exe_dir = os.path.dirname(os.path.abspath(exe_path))
        subprocess.run([os.path.abspath(exe_path)], cwd=exe_dir)
    except Exception as e:
        print(f"[red]Erro ao lançar o executável: {e}[/red]")
        return

    # 6. LÊ A TELEMETRIA PÓS-JOGO
    print("\n[cyan]Jogo terminado. A ler telemetria da tua sessão...[/cyan]")
    if not os.path.exists(metrics_path):
        print("[yellow]Aviso: metrics.json não gerado. Nenhuma evolução aplicada.[/yellow]")
        return

    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
    except Exception as e:
        print(f"[red]Erro ao ler as métricas: {e}[/red]")
        return

    campaign_completed = metrics_data.get("campaign_completed", False)
    played_level_id = metrics_data.get("bottleneck_level", 1) if not campaign_completed else 10
    win_rate = 0.0

    for rep in metrics_data.get("level_reports", []):
        if rep.get("level_id") == played_level_id:
            win_rate = rep.get("win_rate", 0.0)
            break

    print(f"[white]Resultado: Nível {played_level_id} | Taxa de Sucesso: {win_rate*100}%[/white]")

    # 7. EVOLUÇÃO HUMAN-CENTRIC
    level_index = next((i for i, lvl in enumerate(campaign) if lvl.get("level_id") == played_level_id), -1)

    if level_index == -1:
        print(f"[red]Erro: Nível {played_level_id} não encontrado na campanha![/red]")
        return

    if win_rate >= 1.0:
        print(f"[bold green]🎉 Passaste o Nível {played_level_id}! Mantendo a dificuldade atual.[/bold green]")
    else:
        print(f"[cyan]A ajustar a dificuldade do Nível {played_level_id} para o teu perfil...[/cyan]")

        # Chama a IA de evolução humana
        evolved_data = evolve_human_genome(config, metrics_data, campaign[level_index])

        if evolved_data and "new_genome" in evolved_data:
            new_genome = evolved_data["new_genome"]
            new_genome["level_id"] = played_level_id

            # Sincroniza a campanha
            campaign[level_index] = new_genome

            # Grava na Produção e sincroniza com o template de trabalho
            with open(level_path, "w", encoding="utf-8") as f:
                json.dump(campaign, f, indent=2)

            # Sincroniza também com a memória central
            with open("templates/json/level_genome.json", "w", encoding="utf-8") as f:
                json.dump(campaign, f, indent=2)

            report_text = evolved_data.get("report", "Evolução manual aplicada.")
            log_evolution_to_db(db_path, metrics_data, new_genome, report_text, True)

            print(f"[bold green]✅ Dificuldade ajustada. Próxima tentativa será mais justa![/bold green]")
if __name__ == "__main__":
    launch_manual_game()