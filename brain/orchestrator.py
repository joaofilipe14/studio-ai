from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import yaml
from rich import print

from brain.planning import request_plan, extract_first_json_object # <-- NOVA IMPORTAÇÃO
from brain.contracts import validate_plan_contract
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

# --- FUNÇÃO EVOLUTIVA ATUALIZADA (Suporta Modos de Jogo) ---
def evolve_game_genome(config: dict, metrics: dict, current_genome: dict) -> Optional[dict]:
    # Detectamos o modo atual para forçar a IA a manter-se nele
    current_mode = current_genome.get("mode", "PointToPoint")

    prompt = f"""
        You are an AI Game Evolution Director. 
        Current Game Genome: {json.dumps(current_genome, indent=2)}
        Simulation Metrics: {json.dumps(metrics, indent=2)}
        
        STRICT RULES:
        1. You MUST keep the "mode" as "{current_mode}". Do not change it.
        2. Your goal is to reach a win_rate between 0.6 and 0.8 (The Sweet Spot).
        3. If introducing or increasing "enemySpeed", you MUST ensure "timeLimit" is sufficient to allow for evasion maneuvers.
        
        ANALYSIS GUIDELINES:
        - If win_rate < 0.6 (Too Hard): 
            * Decrease "enemySpeed".
            * Increase "timeLimit".
            * Decrease "obstacles.count" or "targetCount".
        - If win_rate > 0.8 (Too Easy): 
            * Increase "enemySpeed" (current target: 2.0).
            * Decrease "timeLimit".
            * Increase "obstacles.count" or scale.
        
        INTEGRATION TASK:
        The user wants a challenge with an enemy speed of 2.0. If the current win_rate allows, 
        set "enemySpeed" to 2.0 and balance the "timeLimit" and "agent.speed" so the agent 
        can still complete the objective while being chased.
        
        Return ONLY JSON:
        {{
          "report": "Brief explanation of your balancing strategy",
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
            "temperature": 0.3, # Ligeiro aumento para permitir criatividade na troca de modos
            "top_p": 0.9,
            "num_ctx": 4096
        }
    )
    content = resp["message"]["content"]
    return extract_first_json_object(content)

def main():
    config = load_yaml("config.yaml")
    state_path = config["paths"]["state"]
    log_path = os.path.join(config["paths"]["logs"], f"run-{now_id()}.jsonl")

    db_path = os.path.join(config["paths"]["logs"], "evolution.db")
    init_db(db_path)

    system_prompt = read_prompt("prompts/system.md")
    planner_obj = json.loads(read_prompt("prompts/plan.json"))

    allowed_tools = set(planner_obj.get("constraints", {}).get("allowed_tools", []))
    forbidden_tools = set(planner_obj.get("constraints", {}).get("forbidden_tools", []))

    state = load_state(state_path)

    env = call_tool("env_info", {}, config)
    log_jsonl(log_path, {"event": "env_info", "result": env})
    if not env["ok"]:
        print(f"[red]env_info failed:[/red] {env['output']}")
        return
    env_data = env.get("data") or {}

    goal = (
        "Create a Unity project called game_001 inside projects/game_001. "
        "Steps required: "
        "1) Find Unity Editor using find_unity_editor. "
        "2) Create the project using unity_create_project. "
        "3) Create folder Assets/Editor if missing. "
        "4) Write two C# files: Assets/HelloFromAI.cs and Assets/Editor/BuildScript.cs. "
        "5) Execute headless build using unity_run_execute_method with method BuildScript.MakeBuild. "
        "Do not create snapshots. Return only a JSON plan."
        "Write full compilable C# contents."
    )
    state["goal"] = goal

    max_replans = int(config.get("run", {}).get("max_replans", 2))
    attempt = 0
    last_plan_raw: Optional[str] = None
    last_error: Optional[str] = None

    while attempt <= max_replans:
        if attempt == 0:
            print("[cyan]Planning...[/cyan]")
        else:
            print(f"[yellow]Replanning (attempt {attempt}/{max_replans})...[/yellow] Reason: {last_error}")

        plan, plan_raw = request_plan(
            config=config,
            system_prompt=system_prompt,
            planner_obj=planner_obj,
            env_data=env_data,
            goal=goal,
            log_jsonl=log_jsonl,
            log_path=log_path,
            previous_error=last_error,
            previous_plan_raw=last_plan_raw,
        )
        last_plan_raw = plan_raw

        if not plan or "steps" not in plan:
            last_error = "LLM did not return a usable JSON plan"
            attempt += 1
            continue

        ok, reason = validate_plan_contract(plan, allowed_tools, forbidden_tools)
        if not ok:
            last_error = f"Plan violates contract: {reason}"
            attempt += 1
            continue

        print("[green]Plan accepted. Executing steps...[/green]")

        tool_context: Dict[str, Any] = {}
        all_ok = True
        failure_reason: Optional[str] = None
        wrote_cs = False
        build_succeeded = False
        last_build_args: Optional[Dict[str, Any]] = None

        for step in plan["steps"]:
            for tc in step.get("tool_calls", []):
                tname = tc.get("tool")
                args = tc.get("args", {}) or {}

                out = call_tool(tname, args, config, env_data=env_data, tool_context=tool_context)

                if tname == "write_file" and (args.get("path") or "").replace("\\", "/").lower().endswith(".cs"):
                    wrote_cs = True

                if tname == "unity_run_execute_method":
                    last_build_args = dict(args)
                    if out.get("ok"):
                        build_succeeded = True

                if tname == "find_unity_editor" and out.get("ok") and out.get("data"):
                    if out["data"].get("unity_path"): tool_context["unity_path"] = out["data"]["unity_path"]

                if tname == "unity_create_project" and out.get("ok"):
                    if args.get("project_name"): tool_context["project_name"] = args["project_name"]
                    if args.get("project_path"): tool_context["project_path"] = args["project_path"]

                if not out["ok"]:
                    all_ok = False
                    failure_reason = f"Tool failed: {tname} -> {out.get('output')}"
                    print(f"[red]{failure_reason}[/red]")
                    break
            if not all_ok: break

        if all_ok:
            if wrote_cs and not build_succeeded:
                retry_args = dict(last_build_args or {})
                retry_args.setdefault("method", "BuildScript.MakeBuild")
                if tool_context.get("unity_path") and not retry_args.get("unity_path"): retry_args["unity_path"] = tool_context["unity_path"]
                if tool_context.get("project_path") and not retry_args.get("project_path"): retry_args["project_path"] = tool_context["project_path"]
                retry_args["log_file"] = os.path.join("logs", "unity-build-retry.log")

                retry = call_tool("unity_run_execute_method", retry_args, config, env_data=env_data, tool_context=tool_context)
                if not retry.get("ok"):
                    last_error = f"Build retry failed -> {retry.get('output')}"
                    attempt += 1
                    continue

            print("\n[green]Build OK! Starting Simulation...[/green]")

            # --- FASE 3: SIMULAÇÃO E EVOLUÇÃO ---
            pn = tool_context.get("project_name", "game_001")
            proj_abs = os.path.abspath(os.path.join("projects", pn))
            exe_path = os.path.join(proj_abs, "Builds", "Game001.exe")
            metrics_path = os.path.join(proj_abs, "Builds", "metrics.json")
            genome_path = os.path.join(proj_abs, "Builds", "game_genome.json")

            sim_res = call_tool("run_game_simulation", {"exe_path": exe_path, "metrics_path": metrics_path}, config)

            if sim_res.get("ok"):
                metrics_data = sim_res["data"]["metrics"]
                win_rate = metrics_data.get("win_rate", 0.0)
                print(f"[cyan]Simulation completed. Metrics:[/cyan]\n{json.dumps(metrics_data, indent=2)}")

                # Ler o genoma atual (se não existir cria um default de base)
                current_genome = {}
                if os.path.exists(genome_path):
                    with open(genome_path, "r", encoding="utf-8") as f:
                        current_genome = json.load(f)
                else:
                    current_genome = {
                        "seed": 42,
                        "arena": {"halfSize": 8.0, "walls": True},
                        "agent": {"speed": 5.0, "acceleration": 15.0, "stopDistance": 0.5},
                        "obstacles": {"count": 8, "minScale": 1.0, "maxScale": 2.5},
                        "rules": {"timeLimit": 20.0, "rounds": 5}
                    }
                if 0.6 <= win_rate <= 0.8:
                    hall_of_fame_dir = os.path.join("hall_of_fame")
                    os.makedirs(hall_of_fame_dir, exist_ok=True)

                    seed = current_genome.get("seed", "unknown")
                    hof_filename = os.path.join(hall_of_fame_dir, f"genome_seed_{seed}_wr_{win_rate:.2f}.json")

                    with open(hof_filename, "w", encoding="utf-8") as hof_file:
                        json.dump(current_genome, hof_file, indent=2)

                    print(f"[bold yellow]🏆 HALL OF FAME! Win rate {win_rate} is ideal. Genome saved to {hof_filename}[/bold yellow]")
                print("\n[magenta]Asking AI Director to EVOLVE the game genome...[/magenta]")
                evolved_data = evolve_game_genome(config, metrics_data, current_genome)

                if evolved_data and "new_genome" in evolved_data:
                    new_genome = evolved_data["new_genome"]
                    # Força uma nova seed para mudar as posições no próximo nível
                    new_genome["seed"] = current_genome.get("seed", 42) + 1

                    # Escreve o novo Genoma por cima do antigo!
                    call_tool("write_file", {"path": genome_path, "content": json.dumps(new_genome, indent=2)}, config)
                    report_text = evolved_data.get('report', 'No report text provided.')
                    log_evolution_to_db(db_path, metrics_data, new_genome, report_text)
                    print(f"\n[bold magenta]=== AI EVOLUTION REPORT ===[/bold magenta]")
                    print(f"Report: {evolved_data.get('report', 'No report text provided.')}")
                    print(f"\n[bold green]New Genome Saved to {genome_path}! Next build will use these values:[/bold green]")
                    print(json.dumps(new_genome, indent=2))
                else:
                    print("[red]AI failed to generate a valid JSON genome. Sticking to current version.[/red]")
            else:
                print(f"[yellow]Simulation failed to run or export metrics: {sim_res.get('output')}[/yellow]")
            # ------------------------------------------------

            state["last_result"] = "ok"
            state["history"].append({"ts": now_id(), "result": "ok"})
            save_state(state_path, state)
            return

        last_error = failure_reason or "Execution failed"
        attempt += 1

    print(f"[red]Failed after {max_replans} replans.[/red]")
    state["last_result"] = "fail"
    save_state(state_path, state)

if __name__ == "__main__":
    main()