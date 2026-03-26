from __future__ import annotations

from datetime import datetime

import json
import os
import time
import random
import yaml
import shutil
from rich import print

from shared.db.economy_logger import log_economy_snapshot, init_economy_db
from shared.tool_runner import call_tool
from shared.db.evolution_logger import init_db, log_evolution_to_db
from services.game_director.logic import evolve_bot_genome, evolve_economy


def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_state(path: str):
    if not os.path.exists(path):
        return {"goal": "bootstrapping", "history": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(path: str, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def now_id():
    return time.strftime("%Y%m%d-%H%M%S")


def main(visible_run=False):
    config = load_yaml("config.yaml")
    state_path = config["paths"]["state"]
    db_path = os.path.join(config["paths"]["data"], "evolution.db")
    init_db(db_path)
    init_economy_db(db_path)

    state = load_state(state_path)

    print("[cyan]A inicializar o AI Director (Campaign Workflow)...[/cyan]")

    # 1. DEFINIÇÃO DE CAMINHOS
    pn = "game_001"

    projects_dir = config.get("paths", {}).get("projects", "workspace/projects")
    proj_abs = os.path.abspath(os.path.join(projects_dir, pn))

    exe_path = os.path.join(proj_abs, "Builds", "Game001.exe")
    metrics_path = os.path.join(proj_abs, "Builds", "metrics.json")

    # Os Caminhos VERDADEIROS para a IA ler (Na Build)
    campaign_path = os.path.join(proj_abs, "Builds", "level_genome.json")
    roster_path = os.path.join(proj_abs, "Builds", "roster.json")
    safe_room_path = os.path.join(proj_abs, "Builds", "safe_room_items.json")
    player_save_path = os.path.join(proj_abs, "Builds", "player_save.json") # 🚨 NOVO: Caminho do Save

    # Caminhos dos Templates Originais
    template_campaign_path = os.path.join("templates", "json", "level_genome.json")
    template_roster_path = os.path.join("templates", "json", "roster.json")
    template_safe_room_path = os.path.join("templates", "json", "safe_room_items.json")

    tool_context = {
        "project_name": pn,
        "project_path": proj_abs
    }

    # 2. SETUP DO PROJETO E BUILD (ESTÁTICO)
    if not os.path.exists(exe_path):
        print(f"[yellow]Build não encontrada em {exe_path}. A iniciar Setup Inicial...[/yellow]")

        res_unity = call_tool("find_unity_editor", {}, config, tool_context=tool_context)
        if res_unity.get("ok") and res_unity.get("data"):
            tool_context["unity_path"] = res_unity["data"].get("unity_path")

        res_create = call_tool("unity_create_project", {"project_name": pn}, config, tool_context=tool_context)
        if not res_create.get("ok"):
            print(f"[red]Erro ao criar o projeto: {res_create.get('output')}[/red]")
            return

        print("[yellow]A compilar o Unity (isto pode demorar alguns minutos)...[/yellow]")
        res_build = call_tool("unity_run_execute_method", {
            "method": "BuildScript.MakeBuild"
        }, config, tool_context=tool_context)

        if not res_build.get("ok"):
            print(f"[red]Erro fatal na Build: {res_build.get('output')}[/red]")
            return

        print("[green]Setup e Build concluídos com sucesso![/green]")
    else:
        print("[green]Projeto e Build encontrados! A saltar fase de compilação.[/green]")


    # 2.5 GARANTIR QUE OS JSONS EXISTEM NA BUILD ANTES DE JOGAR
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
            else:
                print(f"[red]Aviso: Template de {name} não encontrado em {tpl_path}![/red]")

    # 3. FASE DE SIMULAÇÃO
    print("\n[green]A iniciar Simulação QA (Bot)...[/green]")

    sim_args = ["-botMode"]
    if not visible_run:
        sim_args.extend(["-batchmode", "-nographics"])

    sim_res = call_tool("run_game_simulation", {
        "exe_path": exe_path,
        "metrics_path": metrics_path,
        "args": sim_args
    }, config)

    if not sim_res.get("ok"):
        print(f"[red]Erro na simulação: {sim_res.get('output')}[/red]")
        return

    metrics_data = sim_res["data"]["metrics"]
    campaign_completed = metrics_data.get("campaign_completed", False)
    is_human_run = False
    level_reports = metrics_data.get("level_reports", [])

    print(f"[cyan]Simulação concluída. Foram jogados {len(level_reports)} níveis. A iniciar análise profunda...[/cyan]")

    # 4. CARREGAR OS DADOS ATUAIS PARA MEMÓRIA (DA BUILD!)
    with open(campaign_path, "r", encoding="utf-8") as f:
        campaign = json.load(f)
    if isinstance(campaign, dict):
        campaign = [campaign]

    current_roster = None
    if os.path.exists(roster_path):
        with open(roster_path, "r", encoding="utf-8") as f:
            current_roster = json.load(f)

    safe_room_data = None
    if os.path.exists(safe_room_path):
        with open(safe_room_path, "r", encoding="utf-8") as f:
            safe_room_data = json.load(f)

    # 🚨 LER O PLAYER SAVE DA BUILD!
    current_player_save = {}
    if os.path.exists(player_save_path):
        with open(player_save_path, "r", encoding="utf-8") as f:
            current_player_save = json.load(f)

    current_session = f"Bot_Run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # =========================================================
    # 5. PROCESSAR TODOS OS NÍVEIS JOGADOS NESTA RUN!
    # =========================================================
    for rep in level_reports:
        played_level_id = rep.get("level_id")
        win_rate = rep.get("win_rate", 0.0)
        print(f"\n[bold blue]=======================================[/bold blue]")
        print(f"[bold blue]🔍 A AVALIAR NÍVEL {played_level_id} (Win Rate: {win_rate})[/bold blue]")

        current_level = None
        level_index = -1
        for i, level in enumerate(campaign):
            if level.get("level_id") == played_level_id:
                current_level = level
                level_index = i
                break

        if current_level is None:
            continue

        print(f"[magenta]A pedir ao AI Director para EVOLUIR o Nível {played_level_id}...[/magenta]")
        evolved_data = evolve_bot_genome(config, metrics_data, current_level, current_player_save, current_roster)

        if evolved_data and "new_genome" in evolved_data:
            new_level = evolved_data["new_genome"]

            # 🛡️ BLINDAGEM: Garante que a IA não altera dados essenciais
            new_level["level_id"] = played_level_id
            new_level["theme"] = current_level.get("theme", "Cyberpunk Neon")
            new_level["seed"] = random.randint(10000, 99999)

            campaign[level_index] = new_level
            report_text = evolved_data.get('report', 'Sem relatório.')

            log_evolution_to_db(
                db_path=db_path,
                metrics=metrics_data,
                new_genome=new_level,
                report=report_text,
                is_human=is_human_run,
                session_id=current_session,
                current_roster=current_roster
            )

            print(f"[bold green]✅ Nível {played_level_id} Evoluído com sucesso![/bold green]")
        else:
            print(f"[red]Erro da IA ao gerar genoma para o Nível {played_level_id}.[/red]")

    # =========================================================
    # 8. GRAVAR A CAMPANHA COMPLETA COM AS MUTAÇÕES DESTA RUN
    # =========================================================
    with open(campaign_path, "w", encoding="utf-8") as f:
        json.dump(campaign, f, indent=2)
    print(f"\n[bold cyan]💾 Campanha atualizada e guardada! Pronta para a próxima simulação.[/bold cyan]")

    # =========================================================
    # 9. AVALIAÇÃO DA ECONOMIA (O GESTOR FINANCEIRO IA)
    # =========================================================
    print("\n[magenta]A chamar o Diretor de Economia para ajustar o Mercado...[/magenta]")

    if current_player_save and current_roster and safe_room_data:
        economy_result = evolve_economy(config, metrics_data, current_player_save, current_roster, safe_room_data)

        # Grava o Roster (Cofre)
        current_roster = economy_result.get("new_roster", current_roster)
        with open(roster_path, "w", encoding="utf-8") as f:
            json.dump(current_roster, f, indent=2)

        # Grava o Catálogo (Safe Room)
        safe_room_data = economy_result.get("new_safe_room", safe_room_data)
        with open(safe_room_path, "w", encoding="utf-8") as f:
            json.dump(safe_room_data, f, indent=2)

        print(f"[bold green]📈 {economy_result.get('report', 'Inflação ajustada!')}[/bold green]")

        # Tira uma "Fotografia" aos preços atuais
        prices_snapshot = {}
        for item in current_roster.get("items", []): prices_snapshot[item["id"]] = item["cost"]
        for item in safe_room_data.get("safeRoomItems", []): prices_snapshot[item["id"]] = item["cost"]

        player_coins = current_player_save.get("wallet", {}).get("totalCoins", 0)
        player_crystals = current_player_save.get("wallet", {}).get("timeCrystals", 0)

        log_economy_snapshot(db_path, current_session, player_coins, player_crystals, prices_snapshot)

        print(f"[cyan]📊 Histórico da inflação guardado na Base de Dados (tabela 'economy_history')![/cyan]")
    else:
        print("[yellow]Ficheiros de Save ou Lojas em falta. A saltar o ajuste económico.[/yellow]")

    # =========================================================
    # 10. O VERDADEIRO HALL OF FAME (CAMPANHA COMPLETA VENCEDORA)
    # =========================================================
    if campaign_completed:
        total_deaths = sum(rep.get("lives_lost", 0) for rep in level_reports)
        lives_remaining = current_player_save.get("stats", {}).get("currentLives", 0)

        is_masterpiece = True
        rejection_reason = ""

        # 🚨 Regra 1: O jogo não pode ser um passeio no parque (Tem de ter morrido pelo menos 5 vezes na campanha)
        if total_deaths < 5:
            is_masterpiece = False
            rejection_reason = f"Demasiado fácil. O Bot só perdeu {total_deaths} vidas ao longo de todos os testes."

        # 🚨 Regra 2: O Boss Final tem de deixar o jogador a suar (Não podem sobrar muitas vidas)
        elif lives_remaining > 3:
            is_masterpiece = False
            rejection_reason = f"Sobraram demasiadas vidas ({lives_remaining}) no fim do jogo. Falta tensão dramática!"

        hall_of_fame_dir = config.get("paths", {}).get("hall_of_fame", "workspace/hall_of_fame")
        target_dir = os.path.abspath(hall_of_fame_dir)
        os.makedirs(target_dir, exist_ok=True)

        if is_masterpiece:
            hof_filename = os.path.join(target_dir, f"campaign_masterpiece_{now_id()}.json")
            with open(hof_filename, "w", encoding="utf-8") as hof_file:
                json.dump(campaign, hof_file, indent=2)
            shutil.copy2(roster_path, os.path.join(target_dir, "roster.json"))
            shutil.copy2(safe_room_path, os.path.join(target_dir, "safe_room_items.json"))

            print(f"\n[bold yellow]🏆 THE TRUE HALL OF FAME! Masterpiece Validada![/bold yellow]")
            print(f"[bold yellow]👑 Campanha e Economia de Ouro guardadas com rigor na pasta Hall of Fame![/bold yellow]")
        else:
            print(f"\n[bold red]🚫 O Bot concluiu a Campanha, mas NÃO é uma Masterpiece![/bold red]")
            print(f"[yellow]Motivo: {rejection_reason}[/yellow]")
            print(f"[yellow]A apagar o Save do Bot para o forçar a treinar esta campanha com novas mutações...[/yellow]")

            # Apaga o save do Bot para o obrigar a recomeçar a escalar a dificuldade
            if os.path.exists(player_save_path):
                os.remove(player_save_path)

    state["last_result"] = "ok"
    state["history"].append({"ts": now_id(), "result": "ok"})
    save_state(state_path, state)

    # =========================================================
    # 11. SINCRONIZAÇÃO COM A RAIZ DO PROJETO (VISIBILIDADE)
    # =========================================================
    print("\n[cyan]🔄 A sincronizar os ficheiros evoluídos com a raiz do projeto...[/cyan]")

    root_campaign_path = os.path.join(proj_abs, "level_genome.json")
    root_roster_path = os.path.join(proj_abs, "roster.json")
    root_safe_room_path = os.path.join(proj_abs, "safe_room_items.json")
    root_player_save_path = os.path.join(proj_abs, "player_save.json")

    if os.path.exists(campaign_path): shutil.copy2(campaign_path, root_campaign_path)
    if os.path.exists(roster_path): shutil.copy2(roster_path, root_roster_path)
    if os.path.exists(safe_room_path): shutil.copy2(safe_room_path, root_safe_room_path)
    if os.path.exists(player_save_path): shutil.copy2(player_save_path, root_player_save_path)

    print("[bold green]👀 Ficheiros atualizados na raiz do projeto! Já podes abrir os JSONs e confirmar as mutações.[/bold green]")