from __future__ import annotations

import json
import os
import time
import random
import yaml
from rich import print

from shared.tool_runner import call_tool
from shared.db.evolution_logger import init_db, log_evolution_to_db
from services.game_director.logic import evolve_bot_genome
# Importamos a personalidade BOT do nosso novo Cérebro Central


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

def log_jsonl(log_path: str, obj):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main():
    config = load_yaml("config.yaml")
    state_path = config["paths"]["state"]
    db_path = os.path.join(config["paths"]["data"], "evolution.db")
    init_db(db_path)

    state = load_state(state_path)

    print("[cyan]A inicializar o AI Director (Campaign Workflow)...[/cyan]")

    # 1. DEFINIÇÃO DE CAMINHOS
    pn = "game_001"

    # 🎯 Lemos o caminho dos projetos diretamente do YAML (se não existir, usa "workspace/projects")
    projects_dir = config.get("paths", {}).get("projects", "workspace/projects")
    proj_abs = os.path.abspath(os.path.join(projects_dir, pn))

    exe_path = os.path.join(proj_abs, "Builds", "Game001.exe")
    metrics_path = os.path.join(proj_abs, "Builds", "metrics.json")

    # O Caminho VERDADEIRO para a Campanha (A que o Unity lê)
    campaign_path = os.path.join(proj_abs, "Builds", "level_genome.json")

    # Caminho do Template Original
    template_campaign_path = os.path.join("templates", "json", "level_genome.json")

    # Variável de contexto para as tools saberem onde trabalhar
    tool_context = {
        "project_name": pn,
        "project_path": proj_abs
    }

    # 2. BYPASS / SETUP DO PROJETO E BUILD (ESTÁTICO)
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


    # 2.5 GARANTIR QUE A CAMPANHA EXISTE NA BUILD ANTES DE JOGAR
    if not os.path.exists(campaign_path):
        print(f"[yellow]Campanha não encontrada em {campaign_path}. A copiar do Template...[/yellow]")
        if os.path.exists(template_campaign_path):
            os.makedirs(os.path.dirname(campaign_path), exist_ok=True)
            import shutil
            shutil.copy2(template_campaign_path, campaign_path)
            print("[green]Campanha base copiada do template com sucesso![/green]")
        else:
            print(f"[red]ERRO CRÍTICO: Template da campanha também não encontrado em {template_campaign_path}![/red]")
            return

    # 3. FASE DE SIMULAÇÃO
    print("\n[green]A iniciar Simulação QA (Bot)...[/green]")

    sim_res = call_tool("run_game_simulation", {"exe_path": exe_path, "metrics_path": metrics_path}, config)

    if not sim_res.get("ok"):
        print(f"[red]Erro na simulação: {sim_res.get('output')}[/red]")
        return

    metrics_data = sim_res["data"]["metrics"]
    campaign_completed = metrics_data.get("campaign_completed", False)
    is_human_run = False
    level_reports = metrics_data.get("level_reports", [])

    print(f"[cyan]Simulação concluída. Foram jogados {len(level_reports)} níveis. A iniciar análise profunda...[/cyan]")

    # 4. LER A CAMPANHA INTEIRA (O Array JSON)
    if os.path.exists(campaign_path):
        with open(campaign_path, "r", encoding="utf-8") as f:
            campaign = json.load(f)
        if isinstance(campaign, dict):
            campaign = [campaign]
    else:
        print(f"[red]ERRO: O ficheiro {campaign_path} não foi encontrado na raiz![/red]")
        return

    # =========================================================
    # 5. PROCESSAR TODOS OS NÍVEIS JOGADOS NESTA RUN!
    # =========================================================
    for rep in level_reports:
        played_level_id = rep.get("level_id")
        win_rate = rep.get("win_rate", 0.0)
        played_mode = rep.get("mode", "PointToPoint")

        print(f"\n[bold blue]=======================================[/bold blue]")
        print(f"[bold blue]🔍 A AVALIAR NÍVEL {played_level_id} (Modo: {played_mode} | Win Rate: {win_rate})[/bold blue]")

        current_level = None
        level_index = -1
        for i, level in enumerate(campaign):
            if level.get("level_id") == played_level_id:
                current_level = level
                level_index = i
                break

        if current_level is None:
            print(f"[red]Aviso: Nível {played_level_id} não encontrado na campanha. A ignorar...[/red]")
            continue

        # 6. VERIFICAÇÃO DE EQUILÍBRIO (Sweet Spot)
        if 0.6 <= win_rate <= 0.8:
            # O nível está bom! Não chamamos o Ollama para o estragar.
            # Apenas gravamos na BD que ele está porreiro e mudamos a Semente para variar o labirinto.
            log_evolution_to_db(db_path, metrics_data, current_level, "Nível perfeitamente equilibrado (Sweet Spot). Mantido sem mutações.", is_human_run)

            current_level["seed"] = random.randint(10000, 99999)
            campaign[level_index] = current_level

            print(f"[bold yellow]⚡ Nível {played_level_id} equilibrado! Mantido sem mutações de dificuldade.[/bold yellow]")

        # 7. EVOLUÇÃO (Nível desequilibrado: Muito Fácil ou Muito Difícil)
        else:
            print(f"[magenta]A pedir ao AI Director para EVOLUIR o Nível {played_level_id}...[/magenta]")

            evolved_data = evolve_bot_genome(config, metrics_data, current_level)

            if evolved_data and "new_genome" in evolved_data:
                new_level = evolved_data["new_genome"]

                # 🛡️ BLINDAGEM: Garante que a IA não altera dados essenciais
                new_level["level_id"] = played_level_id
                new_level["mode"] = current_level.get("mode", "PointToPoint")
                new_level["theme"] = current_level.get("theme", "Cyberpunk Neon")
                new_level["seed"] = random.randint(10000, 99999)

                campaign[level_index] = new_level
                report_text = evolved_data.get('report', 'Sem relatório.')

                log_evolution_to_db(db_path, metrics_data, new_level, report_text, is_human_run)

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
    # 9. O VERDADEIRO HALL OF FAME (CAMPANHA COMPLETA VENCEDORA)
    # =========================================================
    if campaign_completed:
        # 🎯 Lemos o caminho do Hall of Fame diretamente do YAML
        hall_of_fame_dir = config.get("paths", {}).get("hall_of_fame", "workspace/hall_of_fame")
        os.makedirs(hall_of_fame_dir, exist_ok=True)

        # Guarda a Campanha inteira (o array de 10 níveis)
        hof_filename = os.path.join(hall_of_fame_dir, f"campaign_masterpiece_{now_id()}.json")
        with open(hof_filename, "w", encoding="utf-8") as hof_file:
            json.dump(campaign, hof_file, indent=2)

        print(f"\n[bold yellow]🏆 THE TRUE HALL OF FAME! O Bot conseguiu vencer o Nível 10![/bold yellow]")
        print(f"[bold yellow]👑 Campanha de Ouro guardada em: {hof_filename}[/bold yellow]")

    # Gravação de estado final
    state["last_result"] = "ok"
    state["history"].append({"ts": now_id(), "result": "ok"})
    save_state(state_path, state)