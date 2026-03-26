import os
import sys
import json
import yaml
import shutil
import time
from rich import print

from shared.tool_runner import call_tool
from services.game_director.logic import evolve_human_genome
from shared.db.evolution_logger import init_db, log_evolution_to_db

def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def now_id():
    return time.strftime("%Y%m%d-%H%M%S")

def launch_manual_game():
    config = load_yaml("config.yaml")

    print("\n[cyan]🎮 A iniciar o Launcher do Studio-AI...[/cyan]")

    # Caminhos Base
    pn = "game_001"
    projects_dir = config.get("paths", {}).get("projects", "workspace/projects")
    proj_abs = os.path.abspath(os.path.join(projects_dir, pn))
    build_exe_path = os.path.join(proj_abs, "Builds", "Game001.exe")

    releases_dir = config.get("paths", {}).get("releases", "workspace/releases")
    release_exe_path = os.path.abspath(os.path.join(releases_dir, "game_prod", "Game001.exe"))

    playing_release = False

    # 🚨 LÓGICA AUTOMÁTICA: Release primeiro, Build se falhar.
    if os.path.exists(release_exe_path):
        print(f"[bold green]✨ Release Final encontrada! A iniciar a Masterpiece...[/bold green]")
        exe_path = release_exe_path
        metrics_path = os.path.join(os.path.dirname(release_exe_path), "metrics.json")
        playing_release = True
    elif os.path.exists(build_exe_path):
        print(f"[bold yellow]⚠️ Release não encontrada. A iniciar a Versão de Desenvolvimento (Build)...[/bold yellow]")
        exe_path = build_exe_path
        metrics_path = os.path.join(proj_abs, "Builds", "metrics.json")
    else:
        print("[red]Erro: Nenhum executável encontrado (nem Release nem Build). Compila o jogo primeiro![/red]")
        return

    # Garante que a BD existe se formos treinar a IA
    if not playing_release:
        db_path = os.path.join(config["paths"]["data"], "evolution.db")
        init_db(db_path)

        # Caminhos de dados da Build
        campaign_path = os.path.join(proj_abs, "Builds", "level_genome.json")
        roster_path = os.path.join(proj_abs, "Builds", "roster.json")
        player_save_path = os.path.join(proj_abs, "Builds", "player_save.json")
        safe_room_path = os.path.join(proj_abs, "Builds", "safe_room_items.json")

        template_campaign_path = os.path.join("templates", "json", "level_genome.json")
        template_roster_path = os.path.join("templates", "json", "roster.json")
        template_safe_room_path = os.path.join("templates", "json", "safe_room_items.json")

        # Garante que os JSONs existem na Build antes de jogar
        for tpl_path, target_path, name in [
            (template_campaign_path, campaign_path, "Campanha"),
            (template_roster_path, roster_path, "Roster"),
            (template_safe_room_path, safe_room_path, "Safe Room")
        ]:
            if not os.path.exists(target_path):
                if os.path.exists(tpl_path):
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    shutil.copy2(tpl_path, target_path)
    current_save_path = os.path.join(os.path.dirname(exe_path), "player_save.json")
    if os.path.exists(current_save_path):
        try:
            with open(current_save_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)

            # Se a variável 'hasSeenTutorial' não existir ou for False, é o save do Bot!
            has_seen = save_data.get("stats", {}).get("hasSeenTutorial", False)
            if not has_seen:
                os.remove(current_save_path)
                print("[bold yellow]🧹 Save antigo (do Bot) apagado! Preparado para uma ronda Humana limpa.[/bold yellow]")
        except Exception as e:
            print(f"[red]Aviso: Não foi possível verificar o save: {e}[/red]")
    # ==========================================
    # CORRER O JOGO (Release ou Build)
    # ==========================================
    sim_res = call_tool("run_game_simulation", {
        "exe_path": exe_path,
        "metrics_path": metrics_path
    }, config)

    if not sim_res.get("ok"):
        print(f"[red]Erro ou jogo fechado prematuramente: {sim_res.get('output')}[/red]")
        return

    # Se estávamos a jogar a Masterpiece, o script acaba aqui para não estragar a campanha perfeita!
    if playing_release:
        print("\n[bold green]🏆 Jogo da Masterpiece concluído! A campanha final permanece intacta.[/bold green]")
        return

    # ==========================================
    # EVOLUÇÃO IA (Apenas se jogou a Build)
    # ==========================================
    metrics_data = sim_res["data"]["metrics"]
    level_reports = metrics_data.get("level_reports", [])

    if not level_reports:
        print("[yellow]Não foram geradas métricas. Nenhuma evolução aplicada.[/yellow]")
        return

    print(f"\n[cyan]Jogo terminado. Foram jogados {len(level_reports)} níveis. O Diretor IA vai analisar o teu desempenho...[/cyan]")

    with open(campaign_path, "r", encoding="utf-8") as f:
        campaign = json.load(f)
    if isinstance(campaign, dict):
        campaign = [campaign]

    current_roster = {}
    if os.path.exists(roster_path):
        with open(roster_path, "r", encoding="utf-8") as f:
            current_roster = json.load(f)

    current_player_save = {}
    if os.path.exists(player_save_path):
        with open(player_save_path, "r", encoding="utf-8") as f:
            current_player_save = json.load(f)

    current_session = f"Human_Run_{now_id()}"

    for rep in level_reports:
        played_level_id = rep.get("level_id")
        lives_lost = rep.get("lives_lost", 0)

        print(f"\n[bold blue]=======================================[/bold blue]")
        print(f"[bold blue]👤 A AVALIAR O TEU NÍVEL {played_level_id} (Mortes: {lives_lost})[/bold blue]")

        level_index = -1
        for i, level in enumerate(campaign):
            if level.get("level_id") == played_level_id:
                level_index = i
                break

        if level_index == -1: continue

        print(f"[magenta]O AI Director está a moldar o Nível {played_level_id} para a tua próxima tentativa...[/magenta]")

        evolved_data = evolve_human_genome(config, metrics_data, campaign[level_index], current_player_save, current_roster)

        if evolved_data and "new_genome" in evolved_data:
            new_level = evolved_data["new_genome"]
            new_level["level_id"] = played_level_id
            new_level["theme"] = campaign[level_index].get("theme", "Cyberpunk Neon")

            campaign[level_index] = new_level
            report_text = evolved_data.get('report', 'Sem relatório.')

            log_evolution_to_db(
                db_path=db_path,
                metrics=metrics_data,
                new_genome=new_level,
                report=report_text,
                is_human=True,
                session_id=current_session,
                current_roster=current_roster
            )
            print(f"[bold green]✅ Nível {played_level_id} Evoluído![/bold green]")
        else:
            print(f"[red]Erro da IA ao gerar genoma.[/red]")

    with open(campaign_path, "w", encoding="utf-8") as f:
        json.dump(campaign, f, indent=2)

    root_campaign_path = os.path.join(proj_abs, "level_genome.json")
    if os.path.exists(campaign_path):
        shutil.copy2(campaign_path, root_campaign_path)

    print("\n[bold cyan]💾 Campanha atualizada e guardada! O jogo adaptou-se a ti.[/bold cyan]")

if __name__ == "__main__":
    launch_manual_game()