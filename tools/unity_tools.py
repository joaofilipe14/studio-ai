from __future__ import annotations
import os, glob, subprocess
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class ToolResult:
    ok: bool
    output: str
    data: Optional[Dict[str, Any]] = None

def _run(cmd: List[str], cwd: Optional[str] = None, timeout: int = 3600) -> ToolResult:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        return ToolResult(p.returncode == 0, out.strip(), {"returncode": p.returncode})
    except Exception as e:
        return ToolResult(False, f"run error: {e}")

def find_unity_editor() -> ToolResult:
    """
    Tries to locate Unity.exe in common Windows locations.
    Returns best guess path if found.
    """
    candidates = []

    # Common install locations
    patterns = [
        r"C:\Program Files\Unity\Hub\Editor\*\Editor\Unity.exe",
        r"C:\Program Files\Unity Hub\Editor\*\Editor\Unity.exe",
        r"C:\Program Files\Unity Hub\Editor\*\Editor\Unity.exe",
        r"C:\Program Files\Unity\Editor\Unity.exe",
        r"C:\Program Files (x86)\Unity\Hub\Editor\*\Editor\Unity.exe",
        r"C:\Program Files (x86)\Unity Hub\Editor\*\Editor\Unity.exe",
    ]

    for pat in patterns:
        candidates.extend(glob.glob(pat))

    # Deduplicate
    candidates = sorted(set(candidates))
    if not candidates:
        return ToolResult(False, "Unity.exe not found in common paths.", {"candidates": []})

    # Prefer latest version folder name (lexicographic often works: 2022.x > 2021.x)
    best = candidates[-1]
    return ToolResult(True, "ok", {"unity_path": best, "candidates": candidates})

def unity_create_project(
        unity_path: str,
        project_path: Optional[str] = None,
        project_name: Optional[str] = None,
        timeout: int = 3600
) -> ToolResult:
    """
    Creates a new Unity project headless.
    Accepts either:
      - project_path
      - OR project_name (will create under projects/<name>)
    """

    try:
        if not project_path:
            if not project_name:
                return ToolResult(False, "Either project_path or project_name must be provided.")
            project_path = os.path.join("projects", project_name)

        project_path = os.path.abspath(project_path)
        os.makedirs(project_path, exist_ok=True)

        cmd = [
            unity_path,
            "-batchmode",
            "-nographics",
            "-quit",
            "-createProject",
            project_path
        ]

        return _run(cmd, timeout=timeout)

    except Exception as e:
        return ToolResult(False, f"unity_create_project error: {e}")

def unity_run_execute_method(unity_path: str, project_path: str, method: str, log_file: str, timeout: int = 3600) -> ToolResult:
    project_path = os.path.abspath(project_path)
    log_file = os.path.abspath(log_file)
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    cmd = [
        unity_path,
        "-batchmode", "-nographics", "-quit",
        "-projectPath", project_path,
        "-executeMethod", method,
        "-logFile", log_file,
    ]
    return _run(cmd, timeout=timeout)