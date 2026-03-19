import os
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
    print("[cyan]A inicializar o Modo Jogador (Humano)...[/cyan]")

    config = load_yaml("config.yaml")

    # Init DB para guardar evolução Humana também
    db_path = os.path.join(config["paths"]["data"], "evolution.db")
    init_db(db_path)

    pn = "game_001"
    projects_dir = config.get("paths", {}).get("projects", "workspace/projects")
    proj_abs = os.path.abspath(os.path.join(projects_dir, pn))
    exe_path = os.path.join(proj_abs, "Builds", "Game001.exe")

    if not os.path.exists(exe_path):
        print(f"[red]Erro: Build não encontrada em {exe_path}. Corre o bot primeiro para compilar o jogo![/red]")
        return

    # Caminhos VERDADEIROS para ler e escrever (Na Build)
    campaign_path = os.path.join(proj_abs, "Builds", "level_genome.json")
    metrics_path = os.path.join(proj_abs, "Builds", "metrics.json")

    # 🚨 NOVO: Caminhos para o Roster e o Player Save
    roster_path = os.path.join(proj_abs, "Builds", "roster.json")
    player_save_path = os.path.join(proj_abs, "Builds", "player_save.json")

    # Caminhos dos Templates Originais
    template_campaign_path = os.path.join("templates", "json", "level_genome.json")
    template_roster_path = os.path.join("templates", "json", "roster.json")
    template_safe_room_path = os.path.join("templates", "json", "safe_room_items.json")
    safe_room_path = os.path.join(proj_abs, "Builds", "safe_room_items.json")

    # Garante que os JSONs existem na Build antes de jogar
    for tpl_path, target_path, name in [
        (template_campaign_path, campaign_path, "Campanha"),
        (template_roster_path, roster_path, "Roster"),
        (template_safe_room_path, safe_room_path, "Safe Room")
    ]:
        if not os.path.exists(target_path):
            print(f"[yellow]{name} não encontrado na Build. A copiar do Template...[/yellow]")
            if os.path.exists(tpl_path):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(tpl_path, target_path)
                print(f"[green]{name} copiado do template com sucesso![/green]")

    print("\n[bold green]A iniciar o Jogo! Mostra à IA o que vales...[/bold green]")
    sim_res = call_tool("run_game_simulation", {
        "exe_path": exe_path,
        "metrics_path": metrics_path
    }, config)

    if not sim_res.get("ok"):
        print(f"[red]Erro ou jogo fechado prematuramente: {sim_res.get('output')}[/red]")
        return

    metrics_data = sim_res["data"]["metrics"]
    level_reports = metrics_data.get("level_reports", [])

    if not level_reports:
        print("[yellow]Não foram geradas métricas (fechaste o jogo logo?). Nenhuma evolução aplicada.[/yellow]")
        return

    print(f"\n[cyan]Jogo terminado. Foram jogados {len(level_reports)} níveis. O Diretor IA vai analisar o teu desempenho...[/cyan]")

    # Carrega a campanha atual
    with open(campaign_path, "r", encoding="utf-8") as f:
        campaign = json.load(f)
    if isinstance(campaign, dict):
        campaign = [campaign]

    # 🚨 NOVO: Carregar o Roster e o Player Save para a IA ler!
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

        if level_index == -1:
            continue

        print(f"[magenta]O AI Director está a moldar o Nível {played_level_id} para a tua próxima tentativa...[/magenta]")

        # 🚨 CORREÇÃO DO ERRO: Passar o player_save e o roster!
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

    # Gravar a Campanha Evoluída
    with open(campaign_path, "w", encoding="utf-8") as f:
        json.dump(campaign, f, indent=2)

    # Sincronizar de volta para o projeto
    root_campaign_path = os.path.join(proj_abs, "level_genome.json")
    if os.path.exists(campaign_path):
        shutil.copy2(campaign_path, root_campaign_path)

    print("\n[bold cyan]💾 Campanha atualizada e guardada! O jogo adaptou-se a ti.[/bold cyan]")

if __name__ == "__main__":
    launch_manual_game()