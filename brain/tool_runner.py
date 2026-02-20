from __future__ import annotations

import os
from typing import Any, Dict, Optional

from tools.local_tools import (
    env_info,
    list_dir,
    read_file,
    write_file,
    run_cmd,
    snapshot_create,
    snapshot_restore,
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

    # if still contains template variables, drop it to avoid weird paths
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
    # run_cmd: normalize + ignore "save build log" step + idempotent mkdir
    # -----------------------------
    if name == "run_cmd":
        args = normalize_run_cmd_args(args, env_data)

        cmd_list = args.get("cmd", [])
        cmd_str = " ".join(str(x) for x in cmd_list).lower()

        # Some pipelines try to copy/move the unity log afterwards.
        # But unity_run_execute_method already writes the log_file directly.
        if "unity-build" in cmd_str and any(k in cmd_str for k in ["copy", "cp ", "move", "mv "]):
            return {
                "ok": True,
                "output": "log save step ignored (log_file already written by unity_run_execute_method).",
                "data": None,
            }

        # Make mkdir idempotent (works even if tool env is limited)
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
        # unity_path from context
        if not args.get("unity_path") and tool_context.get("unity_path"):
            args["unity_path"] = tool_context["unity_path"]

        # project_path from project_name
        if not args.get("project_path"):
            pn = args.get("project_name") or tool_context.get("project_name")
            if isinstance(pn, str) and pn.strip():
                args["project_path"] = os.path.join("projects", pn.strip())

        # project_path from context
        if not args.get("project_path") and tool_context.get("project_path"):
            args["project_path"] = tool_context["project_path"]

        if name == "unity_run_execute_method":
            # alias: method_name -> method
            if "method" not in args and "method_name" in args:
                args["method"] = args.pop("method_name")

            # default log file
            if not args.get("log_file"):
                pn = args.get("project_name") or tool_context.get("project_name") or "project"
                args["log_file"] = os.path.join("logs", f"unity-build-{pn}.log")

            # fail fast with clear errors (avoid TypeError)
            if not args.get("unity_path"):
                return {
                    "ok": False,
                    "output": "unity_run_execute_method requires unity_path (not found). Run find_unity_editor first.",
                    "data": None,
                }
            if not args.get("project_path"):
                return {
                    "ok": False,
                    "output": "unity_run_execute_method requires project_path (not found). Run unity_create_project first.",
                    "data": None,
                }
            if not args.get("method"):
                return {
                    "ok": False,
                    "output": "unity_run_execute_method requires method (e.g. BuildScript.MakeBuild).",
                    "data": None,
                }

            # --- Preflight: force-write critical scripts from templates ---
            proj = args.get("project_path")
            if isinstance(proj, str) and proj:
                proj_abs = os.path.abspath(proj)

                assets_dir = os.path.join(proj_abs, "Assets")
                editor_dir = os.path.join(assets_dir, "Editor")
                _ensure_dir(assets_dir)
                _ensure_dir(editor_dir)

                preflight_files = [
                    (os.path.join(assets_dir, "Rotator.cs"), "Rotator.cs"),
                    (os.path.join(assets_dir, "HelloFromAI.cs"), "HelloFromAI.cs"),
                    (os.path.join(editor_dir, "BuildScript.cs"), "BuildScript.cs"),
                    # Optional “next steps” scripts (only if templates exist)
                    (os.path.join(assets_dir, "SimpleAgent.cs"), "SimpleAgent.cs"),
                    (os.path.join(assets_dir, "Goal.cs"), "Goal.cs"),
                    (os.path.join(assets_dir, "GameManager.cs"), "GameManager.cs"),
                ]

                for dst, tmpl in preflight_files:
                    try:
                        content = load_template(tmpl)
                    except FileNotFoundError:
                        # If you don't have these templates yet, just skip.
                        # (Rotator/HelloFromAI/BuildScript should exist; others optional.)
                        if tmpl in ("SimpleAgent.cs", "Goal.cs"):
                            continue
                        return {"ok": False, "output": f"Missing template {tmpl} in {TEMPLATES_DIR}", "data": None}
                    except Exception as e:
                        return {"ok": False, "output": f"Failed reading template {tmpl}: {e}", "data": None}

                    try:
                        with open(dst, "w", encoding="utf-8") as f:
                            f.write(content)
                    except Exception as e:
                        return {"ok": False, "output": f"Failed to write {dst}: {e}", "data": None}

                # Make sure Unity uses absolute project path
                args["project_path"] = proj_abs
            # ------------------------------------------------------------

    # -----------------------------
    # Snapshot tools paths injection
    # -----------------------------
    if name == "snapshot_create":
        args = {
            "src_dir": ".",
            "backups_dir": config["paths"]["backups"],
            "label": args.get("label", "snapshot"),
        }

    if name == "snapshot_restore":
        args = {
            "backups_dir": config["paths"]["backups"],
            "snapshot_id": args["snapshot_id"],
            "dst_dir": ".",
        }

    # -----------------------------
    # write_file: normalize + validate + deterministic override + mkdir for dirs
    # -----------------------------
    if name == "write_file":
        # aliases
        if "content" not in args:
            if "text" in args:
                args["content"] = args.pop("text")
            elif "data" in args:
                args["content"] = args.pop("data")

        # validate
        if "path" not in args or not isinstance(args.get("path"), str) or not args["path"].strip():
            return {"ok": False, "output": "write_file requires non-empty 'path' (string).", "data": None}
        if "content" not in args or not isinstance(args.get("content"), str):
            return {"ok": False, "output": "write_file requires 'content' (string).", "data": None}

        p_raw = args["path"]
        p_norm = _norm_path(p_raw)

        # If LLM tries to "write" to a directory path, treat it as mkdir -p
        looks_like_dir = (
                p_norm.endswith("/")
                or p_norm.endswith("\\")
                or p_norm.lower().endswith("/assets/editor")
                or p_norm.lower().endswith("/assets/editor/")
        )
        if looks_like_dir:
            if p_norm.lower().startswith("assets/") and tool_context.get("project_path"):
                dir_path = os.path.join(tool_context["project_path"], p_norm)
            else:
                dir_path = p_norm
            try:
                os.makedirs(dir_path, exist_ok=True)
                return {"ok": True, "output": f"mkdir ok: {dir_path}", "data": {"dir": dir_path}}
            except Exception as e:
                return {"ok": False, "output": f"mkdir error: {e}", "data": None}

        # Convert literal "\n" sequences (common LLM bug) for C# files
        if p_norm.lower().endswith(".cs"):
            c = args["content"]
            if "\\n" in c and "\n" not in c:
                args["content"] = c.replace("\\n", "\n").replace("\\t", "\t")

        # Prefix Unity-relative paths with project_path (Assets/...)
        if p_norm.lower().startswith("assets/") and tool_context.get("project_path"):
            args["path"] = os.path.join(tool_context["project_path"], p_norm)

        # Deterministic overrides (templates)
        final_norm = _norm_path(args["path"]).lower()

        def _override_if_matches(endswith_path: str, template_name: str) -> Optional[Dict[str, Any]]:
            if final_norm.endswith(endswith_path):
                try:
                    args["content"] = load_template(template_name)
                except Exception as e:
                    return {"ok": False, "output": f"Failed to load template {template_name}: {e}", "data": None}
            return None

        err = _override_if_matches("/assets/editor/buildscript.cs", "BuildScript.cs")
        if err:
            return err
        err = _override_if_matches("/assets/hellofromai.cs", "HelloFromAI.cs")
        if err:
            return err
        err = _override_if_matches("/assets/rotator.cs", "Rotator.cs")
        if err:
            return err
        err = _override_if_matches("/assets/simpleagent.cs", "SimpleAgent.cs")
        if err:
            return err
        err = _override_if_matches("/assets/goal.cs", "Goal.cs")
        if err:
            return err
        err = _override_if_matches("/assets/gamemanager.cs", "GameManager.cs")
        if err:
            return err

    # Execute tool normally
    res = TOOLS[name](**args)
    return {"ok": res.ok, "output": res.output, "data": res.data}