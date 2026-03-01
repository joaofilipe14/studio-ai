from __future__ import annotations

import json
import os
import time
import random
import yaml
from rich import print

from brain.tool_runner import call_tool
from db.evolution_logger import init_db, log_evolution_to_db

# Importamos a personalidade BOT do nosso novo Cérebro Central
from brain.game_director import evolve_bot_genome


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
    db_path = os.path.join(config["paths"]["logs"], "evolution.db")
    init_db(db_path)

    state = load_state(state_path)

    print("[cyan]A inicializar o AI Director (Campaign Workflow)...[/cyan]")

    # 1. DEFINIÇÃO DE CAMINHOS
    pn = "game_001"
    proj_abs = os.path.abspath(os.path.join("projects", pn))
    exe_path = os.path.join(proj_abs, "Builds", "Game001.exe")
    metrics_path = os.path.join(proj_abs, "Builds", "metrics.json")

    # O Caminho VERDADEIRO para a Campanha (A que o Unity lê)
    campaign_path = os.path.join(proj_abs, "Builds", "level_genome.json")

    # Caminho do Template Original
    template_campaign_path = os.path.join("templates", "unity", "level_genome.json")

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

    # Se não completou, o nível jogado é onde ele encravou. Se completou, é o 10.
    played_level_id = metrics_data.get("bottleneck_level", 1) if not campaign_completed else 10

    # Vamos procurar os dados específicos desse nível na lista de relatórios
    win_rate = 0.0
    played_mode = "PointToPoint"

    for rep in metrics_data.get("level_reports", []):
        if rep.get("level_id") == played_level_id:
            win_rate = rep.get("win_rate", 0.0)
            played_mode = rep.get("mode", "PointToPoint")
            break

    print(f"[cyan]Simulation completed. Gargalo detetado no Nível {played_level_id} ({played_mode}). Win Rate: {win_rate}[/cyan]")

    # 4. LER A CAMPANHA INTEIRA (O Array JSON)
    if os.path.exists(campaign_path):
        with open(campaign_path, "r", encoding="utf-8") as f:
            campaign = json.load(f)
        if isinstance(campaign, dict):
            print("[yellow]Aviso: O ficheiro não era um Array. A convertê-lo para formato de Campanha...[/yellow]")
            campaign = [campaign]

    else:
        print(f"[red]ERRO: O ficheiro {campaign_path} não foi encontrado na raiz![/red]")
        return

    # 5. ENCONTRAR O NÍVEL ESPECÍFICO NA LISTA
    current_level = None
    level_index = -1
    for i, level in enumerate(campaign):
        if level.get("level_id") == played_level_id:
            current_level = level
            level_index = i
            break

    if current_level is None:
        print(f"[red]ERRO: O Nível {played_level_id} reportado pelo Unity não existe na campanha![/red]")
        return


    # =========================================================
    # 6. VERIFICAÇÃO RIGOROSA DO HALL OF FAME
    # =========================================================
    if 0.6 <= win_rate <= 0.8:
        hall_of_fame_dir = os.path.join("hall_of_fame")
        os.makedirs(hall_of_fame_dir, exist_ok=True)

        seed = current_level.get("seed")
        if not seed or seed == "unknown" or seed == 0:
            seed = random.randint(10000, 99999)
            current_level["seed"] = seed
            campaign[level_index] = current_level

        hof_filename = os.path.join(hall_of_fame_dir, f"level_{played_level_id}_mode_{played_mode}_seed_{seed}.json")

        # Guarda o nível isolado como Masterpiece
        with open(hof_filename, "w", encoding="utf-8") as hof_file:
            json.dump(current_level, hof_file, indent=2)

        # Grava a campanha atualizada com a nova seed
        with open(campaign_path, "w", encoding="utf-8") as f:
            json.dump(campaign, f, indent=2)

        print(f"\n[bold yellow]🏆 HALL OF FAME MASTERPIECE! O nível {played_level_id} ({played_mode}) está perfeitamente equilibrado ({win_rate})! Guardado em {hof_filename}[/bold yellow]")


    # =========================================================
    # 7. EVOLUÇÃO (Evoluir apenas ESTE nível na lista)
    # =========================================================
    else:
        print(f"\n[magenta]Asking AI Director to EVOLVE Level {played_level_id} ('{played_mode}')...[/magenta]")

        evolved_data = evolve_bot_genome(config, metrics_data, current_level)

        if evolved_data and "new_genome" in evolved_data:
            new_level = evolved_data["new_genome"]

            # 🛡️ BLINDAGEM: Garante que a IA não altera dados essenciais
            new_level["level_id"] = played_level_id
            new_level["mode"] = played_mode
            new_level["theme"] = current_level.get("theme", "Cyberpunk Neon")
            new_level["seed"] = random.randint(10000, 99999)

            # 💉 SUBSTITUI O NÍVEL ANTIGO NA LISTA DA CAMPANHA
            campaign[level_index] = new_level

            # 💾 GRAVA A LISTA INTEIRA DE VOLTA NO level_genome.json
            with open(campaign_path, "w", encoding="utf-8") as f:
                json.dump(campaign, f, indent=2)

            report_text = evolved_data.get('report', 'No report text provided.')
            log_evolution_to_db(db_path, metrics_data, new_level, report_text)

            print(f"\n[bold green]✅ Nível {played_level_id} Evoluído e Gravado na Campanha! A próxima build vai usar as novas regras para este nível.[/bold green]")
        else:
            print("[red]AI failed to generate a valid JSON genome.[/red]")

    # Gravação de estado final
    state["last_result"] = "ok"
    state["history"].append({"ts": now_id(), "result": "ok"})
    save_state(state_path, state)

if __name__ == "__main__":
    main()