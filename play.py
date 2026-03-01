import json
import os
import subprocess
import yaml
from rich import print

from brain.game_director import evolve_human_genome
from db.evolution_logger import init_db, log_evolution_to_db
from scripts.publish import publish_game

def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def launch_manual_test():
    config = load_yaml("config.yaml")
    db_path = os.path.join(config["paths"]["logs"], "evolution.db")
    init_db(db_path)

    release_dir = os.path.join("releases", "game_prod")

    # CAMINHOS
    level_path = os.path.join(release_dir, "level_genome.json")
    save_path = os.path.join(release_dir, "player_save.json")
    exe_path = os.path.join(release_dir, "Game001.exe")
    metrics_path = os.path.join(release_dir, "metrics.json")

    # A LÓGICA DE AUTO-PUBLISH
    if not os.path.exists(exe_path) or not os.path.exists(level_path):
        print(f"[yellow]Aviso: Jogo de produção não encontrado em {release_dir}.[/yellow]")
        print("[cyan]A iniciar a montagem da Release de Produção automaticamente...[/cyan]")
        publish_game()

        if not os.path.exists(exe_path) or not os.path.exists(level_path):
            print("[red]Erro crítico: Falha ao criar a Release. O Orquestrador já fez a primeira build na pasta projects?[/red]")
            return

    # 1. CARREGA A CAMPANHA (O Array)
    try:
        with open(level_path, "r", encoding="utf-8") as f:
            campaign = json.load(f)

        # Blindagem caso o ficheiro antigo (dicionário único) ainda ande por aí
        if isinstance(campaign, dict):
            campaign = [campaign]

    except Exception as e:
        print(f"[red]Erro ao ler o level_genome.json: {e}[/red]")
        return

    # 2. CARREGA O SAVE DO JOGADOR (Para saber em que nível estás)
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
    print("[white]A abrir o jogo... Dá o teu melhor! A IA está a ver.[/white]")

    # 3. LANÇA O JOGO
    try:
        exe_dir = os.path.dirname(os.path.abspath(exe_path))
        subprocess.run([os.path.abspath(exe_path)], cwd=exe_dir)
    except Exception as e:
        print(f"[red]Erro ao lançar o executável: {e}[/red]")
        return

    # 4. LÊ A TELEMETRIA PÓS-JOGO
    print("\n[cyan]Jogo terminado. A ler telemetria da tua sessão...[/cyan]")
    if not os.path.exists(metrics_path):
        print("[yellow]Aviso: metrics.json não gerado pelo jogo. Nenhuma evolução aplicada.[/yellow]")
        return

    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
    except Exception as e:
        print(f"[red]Erro ao ler as métricas: {e}[/red]")
        return

    # Descobre que nível é que jogaste
    played_level_id = metrics_data.get("level_id", 1)
    win_rate = metrics_data.get('win_rate', 0.0)

    print(f"[white]Métricas recebidas: Nível Jogado = {played_level_id} | Win Rate = {win_rate}[/white]")

    # 5. ENCONTRA O NÍVEL NA LISTA
    current_level_genome = None
    level_index = -1
    for i, level in enumerate(campaign):
        if level.get("level_id") == played_level_id:
            current_level_genome = level
            level_index = i
            break

    if current_level_genome is None:
        print(f"[red]Erro: O Nível {played_level_id} reportado não existe no level_genome.json de Produção![/red]")
        return

    # 6. AVALIAÇÃO DA IA (Passa APENAS o nível jogado)
    if win_rate >= 1.0:
        print(f"[bold green]🎉 Passaste o Nível {played_level_id} com sucesso! Não é preciso facilitar o nível.[/bold green]")
        # Como o humano passou, não precisamos de castigar o nível. Mas se quiseres que a IA o torne mais difícil,
        # podes pedir-lhe! Por agora, deixamos seguir.
    else:
        print(f"[cyan]Parece que tiveste dificuldades no Nível {played_level_id}. A pedir ao Diretor de IA para ajustar a dificuldade para ti...[/cyan]")

        evolved_data = evolve_human_genome(config, metrics_data, current_level_genome)

        if evolved_data and "new_genome" in evolved_data:
            new_level_genome = evolved_data["new_genome"]

            # Protege os dados vitais para a IA não estragar a campanha
            new_level_genome["level_id"] = played_level_id
            new_level_genome["mode"] = current_level_genome.get("mode", "PointToPoint")
            new_level_genome["theme"] = current_level_genome.get("theme", "Cyberpunk Neon")

            # Substitui o nível antigo pelo novo na Campanha
            campaign[level_index] = new_level_genome

            # Guarda o ARRAY na pasta de Produção E na raiz do teu workspace
            with open(level_path, "w", encoding="utf-8") as f:
                json.dump(campaign, f, indent=2)

            with open("level_genome.json", "w", encoding="utf-8") as f:
                json.dump(campaign, f, indent=2)

            report_text = evolved_data.get("report", "Sem relatório.")
            log_evolution_to_db(db_path, metrics_data, new_level_genome, report_text)

            print(f"[bold green]✅ Nível {played_level_id} evoluído e gravado! Da próxima vez será mais justo.[/bold green]")
        else:
            print("[red]Falha ao evoluir o nível. Tenta novamente.[/red]")

if __name__ == "__main__":
    launch_manual_test()