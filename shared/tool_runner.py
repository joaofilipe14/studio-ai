from __future__ import annotations
import json
import os
import shutil
from typing import Any, Dict, Optional

from shared.tools.local_tools import (
    env_info, list_dir, read_file, write_file, run_cmd,
    snapshot_create, snapshot_restore, run_game_simulation,
)
from shared.tools.unity_tools import (
    find_unity_editor, unity_create_project, unity_run_execute_method,
)

TOOLS = {
    "env_info": env_info, "list_dir": list_dir, "read_file": read_file, "write_file": write_file,
    "run_cmd": run_cmd, "snapshot_create": snapshot_create, "snapshot_restore": snapshot_restore,
    "find_unity_editor": find_unity_editor, "unity_create_project": unity_create_project,
    "unity_run_execute_method": unity_run_execute_method, "run_game_simulation": run_game_simulation,
}

TEMPLATES_DIR = os.path.join("templates", "unity")

def load_template(filename: str) -> str:
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def normalize_run_cmd_args(args: Dict[str, Any], env_data: Dict[str, Any]) -> Dict[str, Any]:
    args = dict(args or {})
    cmd = args.get("cmd")
    if isinstance(cmd, str): args["cmd"] = cmd.strip().split()
    elif isinstance(cmd, list): args["cmd"] = cmd
    else: args["cmd"] = []
    cwd = args.get("cwd")
    if isinstance(cwd, str) and "${env_info.cwd}" in cwd: args["cwd"] = env_data.get("cwd")
    if isinstance(args.get("cwd"), str) and "${" in args["cwd"]: args.pop("cwd", None)
    return args

def _norm_path(p: str) -> str: return (p or "").replace("\\", "/").strip()
def _ensure_dir(path: str) -> None: os.makedirs(path, exist_ok=True)

def call_tool(name: str, args: dict, config: dict, env_data: Optional[Dict[str, Any]] = None, tool_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    env_data = env_data or {}
    tool_context = tool_context or {}
    args = args or {}

    if name not in TOOLS: return {"ok": False, "output": f"unknown tool: {name}", "data": None}

    if name == "run_cmd":
        args = normalize_run_cmd_args(args, env_data)
        cmd_str = " ".join(str(x) for x in args.get("cmd", [])).lower()
        if "unity-build" in cmd_str and any(k in cmd_str for k in ["copy", "cp ", "move", "mv "]):
            return {"ok": True, "output": "log save step ignored.", "data": None}
        if args.get("cmd") and str(args["cmd"][0]).lower() == "mkdir" and len(args["cmd"]) >= 2:
            path_token = " ".join(str(x) for x in args["cmd"][1:]).strip().strip('"').strip("'")
            try:
                os.makedirs(path_token, exist_ok=True)
                return {"ok": True, "output": f"mkdir ok: {path_token}", "data": {"dir": path_token}}
            except Exception as e: return {"ok": False, "output": f"mkdir error: {e}", "data": None}

    if name in ("unity_create_project", "unity_run_execute_method"):
        if not args.get("unity_path") and tool_context.get("unity_path"): args["unity_path"] = tool_context["unity_path"]
        if not args.get("project_path"):
            if tool_context.get("project_path"): args["project_path"] = tool_context["project_path"]
            else:
                pn = args.get("project_name") or tool_context.get("project_name")
                if pn: args["project_path"] = os.path.join(config.get("paths", {}).get("projects", "workspace/projects"), pn.strip())

        if name == "unity_run_execute_method":
            if "method" not in args and "method_name" in args: args["method"] = args.pop("method_name")
            if not args.get("log_file"):
                pn = args.get("project_name") or tool_context.get("project_name") or "project"
                args["log_file"] = os.path.join(config.get("paths", {}).get("logs", "workspace/logs"), f"unity-build-{pn}.log")

            if not args.get("unity_path") or not args.get("project_path") or not args.get("method"):
                return {"ok": False, "output": "Missing parameters for unity_run_execute_method.", "data": None}

            proj_abs = os.path.abspath(args["project_path"])
            assets_dir = os.path.join(proj_abs, "Assets")
            builds_dir = os.path.join(proj_abs, "Builds")
            editor_dir = os.path.join(assets_dir, "Editor")
            music_dir = os.path.join(assets_dir, "Resources", "Music")
            sprite_dir = os.path.join(assets_dir, "Resources", "Sprites")
            textures_dir = os.path.join(assets_dir, "Resources", "Textures")
            prefabs_dir = os.path.join(assets_dir, "Resources", "Prefabs")
            ui_dir = os.path.join(assets_dir, "Resources", "UI")

            for d in [assets_dir, builds_dir, editor_dir, sprite_dir, music_dir, textures_dir, prefabs_dir, ui_dir]:
                _ensure_dir(d)

            manifest_path = os.path.join(proj_abs, "Packages", "manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)

                    if "dependencies" not in manifest:
                        manifest["dependencies"] = {}

                    manifest["dependencies"]["com.unity.test-framework"] = "1.1.33"

                    with open(manifest_path, "w", encoding="utf-8") as f:
                        json.dump(manifest, f, indent=2)

                    print("[DEBUG] Unity Test Framework injetado no manifest.json!")
                except Exception as e:
                    print(f"[red]Erro ao injetar o Test Framework: {e}[/red]")

            # ==========================================
            # 1. SINCRONIZAÇÃO DINÂMICA DE JSONs
            # ==========================================
            json_folders = [os.path.join("templates", "json"), os.path.join("templates", "unity")]
            for folder in json_folders:
                if os.path.exists(folder):
                    for filename in os.listdir(folder):
                        if filename.endswith(".json"):
                            src_file = os.path.join(folder, filename)
                            if os.path.isfile(src_file):
                                # Copia para o Unity e para a pasta do Build (para ser lido durante o jogo)
                                shutil.copy2(src_file, os.path.join(proj_abs, filename))
                                shutil.copy2(src_file, os.path.join(builds_dir, filename))
                                print(f"[DEBUG] JSON Sincronizado: {filename}")

            # ==========================================
            # 2. SINCRONIZAÇÃO DE ASSETS & UI
            # ==========================================
            folders_to_sync = [
                (os.path.join("templates", "music"), music_dir),
                (os.path.join("templates", "sprites"), sprite_dir),
                (os.path.join("templates", "textures"), textures_dir),
                (os.path.join("templates", "tests"), editor_dir),
                (os.path.join("templates", "ui"), ui_dir) # A UI agora é gerida aqui dentro de forma limpa
            ]

            for src_folder, dst_folder in folders_to_sync:
                if os.path.exists(src_folder):
                    for filename in os.listdir(src_folder):
                        src_file = os.path.join(src_folder, filename)
                        if os.path.isfile(src_file):
                            # Filtro para a pasta UI (só copia .uxml e .uss)
                            if src_folder.endswith("ui") and not (filename.endswith(".uxml") or filename.endswith(".uss")):
                                continue
                            shutil.copy2(src_file, os.path.join(dst_folder, filename))
                            print(f"[DEBUG] Asset Sincronizado: {filename}")

            # ==========================================
            # 3. SINCRONIZAÇÃO DE SCRIPTS C#
            # ==========================================
            if os.path.exists(TEMPLATES_DIR):
                for filename in os.listdir(TEMPLATES_DIR):
                    if filename.endswith(".cs"):
                        dst_path = os.path.join(editor_dir if filename == "BuildScript.cs" else assets_dir, filename)
                        src_path = os.path.join(TEMPLATES_DIR, filename)
                        shutil.copy2(src_path, dst_path)
                        print(f"[DEBUG] Script C# Sincronizado: {filename}")

    if name == "run_game_simulation" and "log_dir" not in args:
        args["log_dir"] = config.get("paths", {}).get("logs", "workspace/logs")

    res = TOOLS[name](**args)
    return {"ok": res.ok, "output": res.output, "data": res.data}