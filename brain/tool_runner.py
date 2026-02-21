from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional

from tools.local_tools import (
    env_info,
    list_dir,
    read_file,
    write_file,
    run_cmd,
    snapshot_create,
    snapshot_restore,
    run_game_simulation,
)
from tools.unity_tools import (
    find_unity_editor,
    unity_create_project,
    unity_run_execute_method,
)

# -----------------------------
# Tools registry
# -----------------------------
TOOLS = {
    "env_info": env_info,
    "list_dir": list_dir,
    "read_file": read_file,
    "write_file": write_file,
    "run_cmd": run_cmd,
    "snapshot_create": snapshot_create,
    "snapshot_restore": snapshot_restore,
    "find_unity_editor": find_unity_editor,
    "unity_create_project": unity_create_project,
    "unity_run_execute_method": unity_run_execute_method,
    "run_game_simulation": run_game_simulation,
}

# -----------------------------
# Template loader
# -----------------------------
TEMPLATES_DIR = os.path.join("templates", "unity")


def load_template(filename: str) -> str:
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# -----------------------------
# Helpers
# -----------------------------
def normalize_run_cmd_args(args: Dict[str, Any], env_data: Dict[str, Any]) -> Dict[str, Any]:
    args = dict(args or {})

    cmd = args.get("cmd")
    if isinstance(cmd, str):
        args["cmd"] = cmd.strip().split()
    elif isinstance(cmd, list):
        args["cmd"] = cmd
    else:
        args["cmd"] = []

    cwd = args.get("cwd")
    if isinstance(cwd, str) and "${env_info.cwd}" in cwd:
        args["cwd"] = env_data.get("cwd")

    if isinstance(args.get("cwd"), str) and "${" in args["cwd"]:
        args.pop("cwd", None)

    return args


def _norm_path(p: str) -> str:
    return (p or "").replace("\\", "/").strip()


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# -----------------------------
# Main dispatch
# -----------------------------
def call_tool(
        name: str,
        args: dict,
        config: dict,
        env_data: Optional[Dict[str, Any]] = None,
        tool_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    env_data = env_data or {}
    tool_context = tool_context or {}
    args = args or {}

    if name not in TOOLS:
        return {"ok": False, "output": f"unknown tool: {name}", "data": None}

    # -----------------------------
    # run_cmd: normalize + ignore "save build log" step
    # -----------------------------
    if name == "run_cmd":
        args = normalize_run_cmd_args(args, env_data)
        cmd_list = args.get("cmd", [])
        cmd_str = " ".join(str(x) for x in cmd_list).lower()

        if "unity-build" in cmd_str and any(k in cmd_str for k in ["copy", "cp ", "move", "mv "]):
            return {
                "ok": True,
                "output": "log save step ignored (log_file already written by unity_run_execute_method).",
                "data": None,
            }

        if isinstance(cmd_list, list) and cmd_list:
            if str(cmd_list[0]).lower() == "mkdir" and len(cmd_list) >= 2:
                path_token = " ".join(str(x) for x in cmd_list[1:]).strip().strip('"').strip("'")
                try:
                    os.makedirs(path_token, exist_ok=True)
                    return {"ok": True, "output": f"mkdir ok (idempotent): {path_token}", "data": {"dir": path_token}}
                except Exception as e:
                    return {"ok": False, "output": f"mkdir error: {e}", "data": None}

    # -----------------------------
    # Unity bindings (last defense)
    # -----------------------------
    if name in ("unity_create_project", "unity_run_execute_method"):
        if not args.get("unity_path") and tool_context.get("unity_path"):
            args["unity_path"] = tool_context["unity_path"]

        if not args.get("project_path"):
            pn = args.get("project_name") or tool_context.get("project_name")
            if isinstance(pn, str) and pn.strip():
                args["project_path"] = os.path.join("projects", pn.strip())

        if not args.get("project_path") and tool_context.get("project_path"):
            args["project_path"] = tool_context["project_path"]

        if name == "unity_run_execute_method":
            if "method" not in args and "method_name" in args:
                args["method"] = args.pop("method_name")

            if not args.get("log_file"):
                pn = args.get("project_name") or tool_context.get("project_name") or "project"
                args["log_file"] = os.path.join("logs", f"unity-build-{pn}.log")

            if not args.get("unity_path"):
                return {"ok": False, "output": "unity_run_execute_method requires unity_path.", "data": None}
            if not args.get("project_path"):
                return {"ok": False, "output": "unity_run_execute_method requires project_path.", "data": None}
            if not args.get("method"):
                return {"ok": False, "output": "unity_run_execute_method requires method.", "data": None}

            # --- Preflight: force-write critical scripts & GENOME ---
            proj = args.get("project_path")
            if isinstance(proj, str) and proj:
                proj_abs = os.path.abspath(proj)
                assets_dir = os.path.join(proj_abs, "Assets")
                editor_dir = os.path.join(assets_dir, "Editor")
                builds_dir = os.path.join(proj_abs, "Builds")

                _ensure_dir(assets_dir)
                _ensure_dir(editor_dir)
                _ensure_dir(builds_dir)

                # 1. Sincronização do Genome (FIX: Injeta se não houver no Build)
                proj_abs = os.path.abspath(proj)
                builds_dir = os.path.join(proj_abs, "Builds")

                # 1. Forçar a criação da pasta Builds AGORA
                if not os.path.exists(builds_dir):
                    os.makedirs(builds_dir, exist_ok=True)

                genome_root = os.path.join(proj_abs, "game_genome.json")
                genome_build = os.path.join(builds_dir, "game_genome.json")

                try:
                    # Tenta ler o genoma que o Python gerou na raiz do workspace
                    if os.path.exists("game_genome.json"):
                        with open("game_genome.json", "r", encoding="utf-8") as f:
                            content = f.read()
                    else:
                        # Se não existir na raiz do workspace, usa o template
                        content = load_template("game_genome.json")

                    # ESCREVE NA RAIZ DO PROJETO (Para o Unity não dar erro no BuildScript)
                    with open(genome_root, "w", encoding="utf-8") as f:
                        f.write(content)

                    # ESCREVE NA PASTA BUILDS (Para o play.py e o .exe)
                    with open(genome_build, "w", encoding="utf-8") as f:
                        f.write(content)

                    print(f"[DEBUG] Genome injetado com sucesso em: {genome_build}")

                except Exception as e:
                    print(f"[ERRO] Falha ao injetar genoma: {e}")

                # 2. Injeção de Scripts
                preflight_files = [
                    (os.path.join(assets_dir, "Rotator.cs"), "Rotator.cs"),
                    (os.path.join(assets_dir, "HelloFromAI.cs"), "HelloFromAI.cs"),
                    (os.path.join(editor_dir, "BuildScript.cs"), "BuildScript.cs"),
                    (os.path.join(assets_dir, "SimpleAgent.cs"), "SimpleAgent.cs"),
                    (os.path.join(assets_dir, "Goal.cs"), "Goal.cs"),
                    (os.path.join(assets_dir, "GameManager.cs"), "GameManager.cs"),
                    (os.path.join(assets_dir, "GameGenome.cs"), "GameGenome.cs"),
                    (os.path.join(assets_dir, "Collectible.cs"), "Collectible.cs"),
                    (os.path.join(assets_dir, "ChaserAI.cs"), "ChaserAI.cs"),
                ]

                for dst, tmpl in preflight_files:
                    try:
                        content = load_template(tmpl)
                        with open(dst, "w", encoding="utf-8") as f:
                            f.write(content)
                    except FileNotFoundError:
                        if tmpl in ("SimpleAgent.cs", "Goal.cs"): continue
                        return {"ok": False, "output": f"Missing template {tmpl}", "data": None}
                    except Exception as e:
                        return {"ok": False, "output": f"Failed writing {tmpl}: {e}", "data": None}

                args["project_path"] = proj_abs

    # -----------------------------
    # Snapshot / Write_file logic
    # -----------------------------
    if name == "snapshot_create":
        args = {"src_dir": ".", "backups_dir": config["paths"]["backups"], "label": args.get("label", "snapshot")}
    if name == "snapshot_restore":
        args = {"backups_dir": config["paths"]["backups"], "snapshot_id": args["snapshot_id"], "dst_dir": "."}

    if name == "write_file":
        if "content" not in args:
            args["content"] = args.pop("text") if "text" in args else args.pop("data")

        p_norm = _norm_path(args["path"])

        # Lógica de diretórios (mkdir)
        if p_norm.endswith("/") or p_norm.endswith("\\") or p_norm.lower().endswith("/assets/editor"):
            dir_path = os.path.join(tool_context["project_path"], p_norm) if tool_context.get("project_path") else p_norm
            _ensure_dir(dir_path)
            return {"ok": True, "output": f"mkdir ok: {dir_path}", "data": {"dir": dir_path}}

        if p_norm.lower().startswith("assets/") and tool_context.get("project_path"):
            args["path"] = os.path.join(tool_context["project_path"], p_norm)

        # Overrides automáticos por templates
        final_norm = _norm_path(args["path"]).lower()
        templates_map = {
            "/assets/editor/buildscript.cs": "BuildScript.cs",
            "/assets/hellofromai.cs": "HelloFromAI.cs",
            "/assets/rotator.cs": "Rotator.cs",
            "/assets/simpleagent.cs": "SimpleAgent.cs",
            "/assets/goal.cs": "Goal.cs",
            "/assets/gamemanager.cs": "GameManager.cs",
            "/assets/gamegenome.cs": "GameGenome.cs",
            "/assets/collectible.cs": "Collectible.cs",
            "/assets/chaserai.cs": "ChaserAI.cs"
        }

        for path_suffix, tmpl_name in templates_map.items():
            if final_norm.endswith(path_suffix):
                try:
                    args["content"] = load_template(tmpl_name)
                except Exception as e:
                    return {"ok": False, "output": f"Failed template {tmpl_name}: {e}"}

    res = TOOLS[name](**args)
    return {"ok": res.ok, "output": res.output, "data": res.data}