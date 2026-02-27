from __future__ import annotations

import json
import os
import time

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

    print("[cyan]A inicializar o AI Director (Static Workflow Bypass)...[/cyan]")

    # 1. DEFINIÇÃO DE CAMINHOS
    pn = "game_001"
    proj_abs = os.path.abspath(os.path.join("projects", pn))
    exe_path = os.path.join(proj_abs, "Builds", "Game001.exe")
    metrics_path = os.path.join(proj_abs, "Builds", "metrics.json")
    genome_path = os.path.join(proj_abs, "Builds", "game_genome.json")

    # Variável de contexto para as tools saberem onde trabalhar
    tool_context = {
        "project_name": pn,
        "project_path": proj_abs
    }

    # 2. BYPASS / SETUP DO PROJETO E BUILD (ESTÁTICO)
    if not os.path.exists(exe_path):
        print(f"[yellow]Build não encontrada em {exe_path}. A iniciar Setup Inicial...[/yellow]")

        # Passo A: Encontrar o Unity
        res_unity = call_tool("find_unity_editor", {}, config, tool_context=tool_context)
        if res_unity.get("ok") and res_unity.get("data"):
            tool_context["unity_path"] = res_unity["data"].get("unity_path")

        # Passo B: Criar o Projeto Unity
        res_create = call_tool("unity_create_project", {"project_name": pn}, config, tool_context=tool_context)
        if not res_create.get("ok"):
            print(f"[red]Erro ao criar o projeto: {res_create.get('output')}[/red]")
            return

        # Passo C: Fazer a Build (Isto aciona o PREFLIGHT no tool_runner.py que copia os Templates!)
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


    # 3. FASE DE SIMULAÇÃO E EVOLUÇÃO
    print("\n[green]A iniciar Simulação QA (Bot)...[/green]")

    sim_res = call_tool("run_game_simulation", {"exe_path": exe_path, "metrics_path": metrics_path}, config)

    if sim_res.get("ok"):
        metrics_data = sim_res["data"]["metrics"]
        win_rate = metrics_data.get("win_rate", 0.0)

        # Saber exatamente qual modo o Unity acabou de reportar
        played_mode = metrics_data.get("currentMode", "PointToPoint")

        print(f"[cyan]Simulation completed ({played_mode}). Metrics:[/cyan]\n{json.dumps(metrics_data, indent=2)}")

        # 1. LER O FICHEIRO COMPLETO DO GENOMA
        full_genome_data = {"configs": []}
        if os.path.exists(genome_path):
            with open(genome_path, "r", encoding="utf-8") as f:
                full_genome_data = json.load(f)

        # Se for o formato antigo (sem configs), cria uma lista default
        if "configs" not in full_genome_data or not isinstance(full_genome_data["configs"], list):
            print("[yellow]Aviso: Formato antigo detetado. A converter para Array...[/yellow]")
            # ... (mantém a tua lista default de configs aqui) ...

        # 2. ENCONTRAR O GENOMA QUE ACABOU DE SER JOGADO
        current_genome = None
        genome_index = 0
        for i, c in enumerate(full_genome_data["configs"]):
            if c.get("mode") == played_mode:
                current_genome = c
                genome_index = i
                break

        if current_genome is not None:
            # ---> A GRANDE MUDANÇA: MEMÓRIA DE WIN RATE <---
            # Guardamos a pontuação atual deste modo específico no JSON
            current_genome["last_win_rate"] = win_rate
            full_genome_data["configs"][genome_index] = current_genome

            # 3. VERIFICAÇÃO RIGOROSA DO HALL OF FAME
            all_modes_balanced = True
            for c in full_genome_data["configs"]:
                # Se um modo ainda não tem 'last_win_rate', assumimos -1.0 (não testado)
                mode_wr = c.get("last_win_rate", -1.0)
                if not (0.6 <= mode_wr <= 0.8):
                    all_modes_balanced = False
                    break # Falhou o teste de perfeição, não vai para o Hall of Fame

            if all_modes_balanced:
                hall_of_fame_dir = os.path.join("hall_of_fame")
                os.makedirs(hall_of_fame_dir, exist_ok=True)
                seed = current_genome.get("seed", "unknown")
                hof_filename = os.path.join(hall_of_fame_dir, f"genome_master_seed_{seed}.json")
                with open(hof_filename, "w", encoding="utf-8") as hof_file:
                    json.dump(full_genome_data, hof_file, indent=2)
                print(f"\n[bold yellow]🏆 HALL OF FAME MASTERPIECE! TODOS os modos ({len(full_genome_data['configs'])}) estão perfeitamente equilibrados! Genoma de ouro guardado em {hof_filename}[/bold yellow]")

            # 4. EVOLUÇÃO (O bot só chateia a IA para evoluir se este modo específico precisar!)
            if not (0.6 <= win_rate <= 0.8):
                print(f"\n[magenta]Asking AI Director to EVOLVE the '{played_mode}' genome...[/magenta]")
                evolved_data = evolve_bot_genome(config, metrics_data, current_genome)
                print(f"\n[bold magenta]=== {evolved_data} ===[/bold magenta]")

                if evolved_data and "new_genome" in evolved_data:
                    new_genome = evolved_data["new_genome"]
                    new_genome["seed"] = current_genome.get("seed", 42) + 1

                    # Como mudámos as regras, apagamos a memória antiga do win_rate para ele ser testado de novo
                    new_genome["last_win_rate"] = -1.0

                    full_genome_data["configs"][genome_index] = new_genome
                    report_text = evolved_data.get('report', 'No report text provided.')
                    log_evolution_to_db(db_path, metrics_data, new_genome, report_text)
                    print(f"\n[bold green]New Genome Array Saved! Next build will use these values.[/bold green]")
                else:
                    print("[red]AI failed to generate a valid JSON genome.[/red]")
            else:
                print(f"\n[green]O modo '{played_mode}' já está balanceado ({win_rate}). A aguardar que os outros modos fiquem prontos...[/green]")

            # 5. GUARDAR O JSON FINAL (Independentemente de ter evoluído ou não)
            call_tool("write_file", {"path": genome_path, "content": json.dumps(full_genome_data, indent=2)}, config)

        else:
            print(f"[red]Erro: O modo {played_mode} retornado pelo Unity não existe no JSON![/red]")

    # Gravação de estado final
    state["last_result"] = "ok"
    state["history"].append({"ts": now_id(), "result": "ok"})
    save_state(state_path, state)