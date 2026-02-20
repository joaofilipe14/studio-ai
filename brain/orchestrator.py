from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import yaml
from rich import print

from brain.planning import request_plan
from brain.contracts import validate_plan_contract
from brain.tool_runner import call_tool


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


def main():
    config = load_yaml("config.yaml")
    state_path = config["paths"]["state"]
    log_path = os.path.join(config["paths"]["logs"], f"run-{now_id()}.jsonl")

    system_prompt = read_prompt("prompts/system.md")
    planner_obj = json.loads(read_prompt("prompts/plan.json"))

    allowed_tools = set(planner_obj.get("constraints", {}).get("allowed_tools", []))
    forbidden_tools = set(planner_obj.get("constraints", {}).get("forbidden_tools", []))

    state = load_state(state_path)

    # Preflight env_info
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
        "Write full compilable C# contents (no placeholders like // build logic here)."
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
            log_jsonl(log_path, {"event": "plan_invalid", "reason": last_error})
            attempt += 1
            continue

        ok, reason = validate_plan_contract(plan, allowed_tools, forbidden_tools)
        if not ok:
            last_error = f"Plan violates contract: {reason}"
            log_jsonl(log_path, {"event": "plan_contract_violation", "reason": last_error, "plan": plan})
            attempt += 1
            continue

        log_jsonl(log_path, {"event": "plan", "plan": plan})
        print("[green]Plan accepted.[/green]")

        tool_context: Dict[str, Any] = {}
        all_ok = True
        failure_reason: Optional[str] = None

        # --- build retry state ---
        wrote_cs = False
        build_succeeded = False
        build_failed_compiler = False
        last_build_args: Optional[Dict[str, Any]] = None

        for step in plan["steps"]:
            print(f"\n[bold]{step.get('id','?')}[/bold] - {step.get('title','')}")
            for tc in step.get("tool_calls", []):
                tname = tc.get("tool")
                args = tc.get("args", {}) or {}

                out = call_tool(tname, args, config, env_data=env_data, tool_context=tool_context)
                log_jsonl(log_path, {"event": "tool_call", "tool": tname, "args": args, "result": out})

                if tname == "write_file":
                    p = (args.get("path") or "").replace("\\", "/").lower()
                    if p.endswith(".cs"):
                        wrote_cs = True

                # Track build attempts and detect compiler-error failure
                if tname == "unity_run_execute_method":
                    last_build_args = dict(args)  # keep the exact args used
                    if out.get("ok"):
                        build_succeeded = True
                    else:
                        o = (out.get("output") or "")
                        if ("Scripts have compiler errors" in o) or ("Script Compilation Error" in o) or ("error CS" in o):
                            build_failed_compiler = True

                # capture unity_path
                if tname == "find_unity_editor" and out.get("ok") and out.get("data"):
                    up = out["data"].get("unity_path")
                    if up:
                        tool_context["unity_path"] = up

                # capture project info
                if tname == "unity_create_project" and out.get("ok"):
                    if args.get("project_name"):
                        tool_context["project_name"] = args["project_name"]
                    if args.get("project_path"):
                        tool_context["project_path"] = args["project_path"]

                if not out["ok"]:
                    all_ok = False
                    failure_reason = f"Tool failed: {tname} -> {out.get('output')}"
                    print(f"[red]{failure_reason}[/red]")
                    break

            if not all_ok:
                break

        if all_ok:
            # If we touched C# files but didn't get a successful build yet, run one build now (same execution)
            if wrote_cs and not build_succeeded:
                # Use the last build args if we have them, otherwise run a default build call
                # Build a safe retry args dict (always include unity_path + project_path when available)
                retry_args = dict(last_build_args or {})
                retry_args.setdefault("method", "BuildScript.MakeBuild")

                # ensure required unity args present
                if tool_context.get("unity_path") and not retry_args.get("unity_path"):
                    retry_args["unity_path"] = tool_context["unity_path"]
                if tool_context.get("project_path") and not retry_args.get("project_path"):
                    retry_args["project_path"] = tool_context["project_path"]
                if tool_context.get("project_name") and not retry_args.get("project_name"):
                    retry_args["project_name"] = tool_context["project_name"]

                # ensure a log file
                if not retry_args.get("log_file"):
                    pn = retry_args.get("project_name") or tool_context.get("project_name") or "project"
                    retry_args["log_file"] = os.path.join("logs", f"unity-build-{pn}.log")

                print("\n[yellow]Post-fix build retry (same run)...[/yellow]")
                retry = call_tool("unity_run_execute_method", retry_args, config, env_data=env_data, tool_context=tool_context)
                log_jsonl(log_path, {"event": "build_retry", "args": retry_args, "result": retry})

                if not retry.get("ok"):
                    # If still failing, treat as failure so replanning can kick in
                    failure_reason = f"Build retry failed -> {retry.get('output')}"
                    print(f"[red]{failure_reason}[/red]")
                    last_error = failure_reason
                    attempt += 1
                    continue
                print("[green]Build retry succeeded.[/green]")

            state["last_result"] = "ok"
            state["history"].append({"ts": now_id(), "result": "ok"})
            save_state(state_path, state)
            print("\n[green]Run OK.[/green]")
            return

        last_error = failure_reason or "Execution failed"
        log_jsonl(log_path, {"event": "execution_failed", "reason": last_error})
        attempt += 1

    print(f"[red]Failed after {max_replans} replans.[/red]")
    state["last_result"] = "fail"
    state["history"].append({"ts": now_id(), "result": "fail"})
    save_state(state_path, state)


if __name__ == "__main__":
    main()