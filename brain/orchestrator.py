from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import yaml
from rich import print

from brain.planning import extract_first_json_object
from brain.tool_runner import call_tool
from brain.ollama_client import chat
from db.evolution_logger import init_db, log_evolution_to_db

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

def read_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def now_id():
    return time.strftime("%Y%m%d-%H%M%S")

def log_jsonl(log_path: str, obj):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# --- FUNÇÃO EVOLUTIVA ATUALIZADA (Lida com o genoma individual extraído da lista) ---
def evolve_game_genome(config: dict, metrics: dict, current_genome: dict) -> Optional[dict]:
    current_mode = current_genome.get("mode", "PointToPoint")

    # Extraímos as novas métricas enviadas pelo Unity
    win_rate = metrics.get("win_rate", 0.0)
    total_collected = metrics.get("total_collected", 0)
    target_count = current_genome.get("rules", {}).get("targetCount", 1)
    total_rounds = metrics.get("total_rounds", 1)

    # Cálculo de eficiência para o modo Collect
    collect_efficiency = (total_collected / (target_count * total_rounds)) if target_count > 0 else 0

    prompt = f"""
        You are an AI Game Evolution Director.
        
        CURRENT CONFIGURATION:
        - Mode: {current_mode}
        - Genome: {json.dumps(current_genome, indent=2)}
        
        LATEST SIMULATION METRICS:
        - Win Rate: {win_rate:.2f}
        - Total Collected Items: {total_collected}
        - Collection Efficiency: {collect_efficiency:.2f} (Items collected vs total possible)
        - Stuck Events: {metrics.get("stuck_events", 0)}
        - Timeouts: {metrics.get("timeouts", 0)}

        STRICT EVOLUTION RULES:
        1. Keep "mode" as "{current_mode}".
        2. Target Win Rate: 0.6 - 0.8 (The Sweet Spot).
        1. IF Win Rate is 1.0: The game is BORING. You MUST make it significantly HARDER.
           - Increase "enemySpeed".
           - Decrease "timeLimit".
           - Increase "obstacles.count" or "trapChance".
       2. IF Win Rate is low (< 0.6): The game is FRUSTRATING. Make it EASIER.
           - Decrease "enemySpeed".
           - Increase "powerUpChance".
        3. Obstacle Scaling: Use "minScale" and "maxScale" to control map density. 
           Higher scales create larger walls/mazes, increasing difficulty.
        
        STRATEGY GUIDELINES:
        - IF Win Rate < 0.6 (Too Hard):
            * If timeouts > 0: Increase "timeLimit".
            * If Collection Efficiency > 0.7: The game is balanced but tight; just add a little more time.
            * If Stuck Events are high: Decrease "obstacles.count" or "maxScale".
            * If agent is caught too often: Decrease "enemySpeed".
        - IF Win Rate > 0.8 (Too Easy):
            * Increase "enemySpeed" (User wants target 2.0).
            * Increase "obstacles.count" or "maxScale" to create tighter corridors.
            * Decrease "timeLimit".

        OUTPUT TASK:
        IMPORTANT: Return ONLY raw JSON. DO NOT include comments like // or any explanatory text inside the JSON structure.
        Balance the game for {current_mode}. Return ONLY a JSON object with:
        {{
          "report": "Analysis of metrics and changes made",
          "new_genome": {{ ... }}
        }}
    """
    messages = [
        {"role": "system", "content": "You are a deterministic AI that outputs ONLY valid JSON. No markdown."},
        {"role": "user", "content": prompt}
    ]

    resp = chat(
        host=config["ollama"]["host"],
        model=config["ollama"]["model"],
        messages=messages,
        options={
            "temperature": 0.3,
            "top_p": 0.9,
            "num_ctx": 4096
        }
    )
    content = resp["message"]["content"]
    print(f"Change game IA response: {content}")
    return extract_first_json_object(content)


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
    print("\n[green]A iniciar Simulação...[/green]")

    sim_res = call_tool("run_game_simulation", {"exe_path": exe_path, "metrics_path": metrics_path}, config)

    if sim_res.get("ok"):
        metrics_data = sim_res["data"]["metrics"]
        win_rate = metrics_data.get("win_rate", 0.0)
        print(f"[cyan]Simulation completed. Metrics:[/cyan]\n{json.dumps(metrics_data, indent=2)}")

        # 1. LER O FICHEIRO COMPLETO DO GENOMA
        full_genome_data = {"configs": []}
        if os.path.exists(genome_path):
            with open(genome_path, "r", encoding="utf-8") as f:
                full_genome_data = json.load(f)

        # Se for o formato antigo (sem configs), cria uma lista default
        if "configs" not in full_genome_data or not isinstance(full_genome_data["configs"], list):
            print("[yellow]Aviso: Formato antigo detetado. A converter para Array...[/yellow]")
            full_genome_data = {
                "configs": [
                    {
                        "mode": "PointToPoint",
                        "seed": 42,
                        "arena": {"halfSize": 10.0, "walls": True},
                        "agent": {"speed": 6.0, "acceleration": 12.0, "stopDistance": 0.5},
                        "obstacles": {"count": 8, "minScale": 1.0, "maxScale": 2.5},
                        "rules": {"timeLimit": 30.0, "rounds": 5, "targetCount": 1, "enemySpeed": 1.0}
                    },
                    {
                        "mode": "Collect",
                        "seed": 99,
                        "arena": {"halfSize": 15.0, "walls": True},
                        "agent": {"speed": 8.0, "acceleration": 15.0, "stopDistance": 0.5},
                        "obstacles": {"count": 12, "minScale": 1.0, "maxScale": 1.5},
                        "rules": {"timeLimit": 45.0, "rounds": 3, "targetCount": 10, "enemySpeed": 0.5}
                    }
                ]
            }

        # 2. DEFINIR QUAL O MODO A EVOLUIR NESTA RUN
        target_mode_to_evolve = full_genome_data.get("mode", "PointToPoint")

        current_genome = None
        genome_index = 0
        for i, c in enumerate(full_genome_data["configs"]):
            if c.get("mode") == target_mode_to_evolve:
                current_genome = c
                genome_index = i
                break

        # Fallback se não encontrar o modo
        if current_genome is None and len(full_genome_data["configs"]) > 0:
            current_genome = full_genome_data["configs"][0]
            genome_index = 0

        # Verificação do Hall of Fame
        if 0.6 <= win_rate <= 0.8:
            hall_of_fame_dir = os.path.join("hall_of_fame")
            os.makedirs(hall_of_fame_dir, exist_ok=True)
            seed = current_genome.get("seed", "unknown")
            hof_filename = os.path.join(hall_of_fame_dir, f"genome_seed_{seed}_wr_{win_rate:.2f}.json")
            with open(hof_filename, "w", encoding="utf-8") as hof_file:
                json.dump(full_genome_data, hof_file, indent=2)
            print(f"[bold yellow]🏆 HALL OF FAME! Win rate {win_rate} is ideal. Genome saved to {hof_filename}[/bold yellow]")

        # Evolução do Genoma
        print(f"\n[magenta]Asking AI Director to EVOLVE the '{current_genome.get('mode')}' genome...[/magenta]")
        evolved_data = evolve_game_genome(config, metrics_data, current_genome)
        print(f"\n[bold magenta]=== {evolved_data} ===[/bold magenta]")

        if evolved_data and "new_genome" in evolved_data:
            new_genome = evolved_data["new_genome"]
            new_genome["seed"] = current_genome.get("seed", 42) + 1

            # 3. SUBSTITUIR APENAS O GENOMA EVOLUÍDO DENTRO DA LISTA
            full_genome_data["configs"][genome_index] = new_genome

            # Escreve o FICHEIRO INTEIRO de volta!
            call_tool("write_file", {"path": genome_path, "content": json.dumps(full_genome_data, indent=2)}, config)

            report_text = evolved_data.get('report', 'No report text provided.')
            log_evolution_to_db(db_path, metrics_data, new_genome, report_text)
            print(f"\n[bold magenta]=== AI EVOLUTION REPORT ===[/bold magenta]")
            print(f"Report: {evolved_data.get('report', 'No report text provided.')}")
            print(f"\n[bold green]New Genome Array Saved! Next build will use these values: {new_genome}[/bold green]")
        else:
            print("[red]AI failed to generate a valid JSON genome. Sticking to current version.[/red]")
    else:
        print(f"[yellow]Simulation failed to run or export metrics: {sim_res.get('output')}[/yellow]")

    # Gravação de estado final
    state["last_result"] = "ok"
    state["history"].append({"ts": now_id(), "result": "ok"})
    save_state(state_path, state)

if __name__ == "__main__":
    main()