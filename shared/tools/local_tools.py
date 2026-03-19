from __future__ import annotations
import os, shutil, subprocess
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import platform, sys

@dataclass
class ToolResult:
    ok: bool
    output: str
    data: Optional[Dict[str, Any]] = None

def list_dir(path: str) -> ToolResult:
    try:
        items = []
        for name in sorted(os.listdir(path)):
            p = os.path.join(path, name)
            items.append({"name": name, "type": "dir" if os.path.isdir(p) else "file"})
        return ToolResult(True, "ok", {"items": items})
    except Exception as e:
        return ToolResult(False, f"list_dir error: {e}")

def read_file(path: str, max_bytes: int = 200_000) -> ToolResult:
    try:
        with open(path, "rb") as f:
            b = f.read(max_bytes)
        return ToolResult(True, "ok", {"content": b.decode("utf-8", errors="replace")})
    except Exception as e:
        return ToolResult(False, f"read_file error: {e}")

def write_file(path: str, content: str) -> ToolResult:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(True, "ok")
    except Exception as e:
        return ToolResult(False, f"write_file error: {e}")

def run_cmd(cmd: List[str], cwd: Optional[str] = None, timeout: int = 900) -> ToolResult:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        return ToolResult(p.returncode == 0, out.strip(), {"returncode": p.returncode})
    except Exception as e:
        return ToolResult(False, f"run_cmd error: {e}")

def snapshot_create(src_dir: str, backups_dir: str, label: str) -> ToolResult:
    try:
        import os, time, shutil

        ts = time.strftime("%Y%m%d-%H%M%S")
        snap_id = f"{ts}-{label}".replace(" ", "_")

        src_abs = os.path.abspath(src_dir)
        backups_abs = os.path.abspath(backups_dir)
        dst = os.path.join(backups_abs, snap_id)
        dst_abs = os.path.abspath(dst)

        os.makedirs(backups_abs, exist_ok=True)

        # Guard: destination cannot be inside source without exclusions
        # (we handle exclusions, but keep this as sanity)
        if os.path.commonpath([src_abs]) == os.path.commonpath([src_abs, dst_abs]):
            # dst is inside src; that's ok ONLY if we ignore backups_dir
            pass

        # Compute which top-level folder name to ignore (e.g. "backups")
        backups_name = os.path.basename(backups_abs.rstrip("\\/"))

        def ignore_func(dirpath: str, names: list[str]) -> set[str]:
            ignore = set()

            # Always ignore these at ANY level
            always_ignore = {
                ".git", ".venv", "__pycache__", ".pytest_cache",
                "logs", "backups",  # common names
            }
            # Also ignore the configured backups folder name (in case you rename it)
            always_ignore.add(backups_name)

            for n in names:
                if n in always_ignore:
                    ignore.add(n)

            # Unity heavy folders (can appear inside projects/*)
            unity_heavy = {"Library", "Temp", "Obj", "Build", "Builds", "UserSettings"}
            for n in names:
                if n in unity_heavy:
                    ignore.add(n)

            return ignore

        shutil.copytree(src_abs, dst_abs, dirs_exist_ok=False, ignore=ignore_func)

        return ToolResult(True, "ok", {"snapshot_id": snap_id, "path": dst_abs})
    except Exception as e:
        return ToolResult(False, f"snapshot_create error: {e}")

def snapshot_restore(backups_dir: str, snapshot_id: str, dst_dir: str) -> ToolResult:
    try:
        src = os.path.join(backups_dir, snapshot_id)
        if not os.path.isdir(src):
            return ToolResult(False, f"snapshot not found: {src}")
        # restore by replacing dst_dir contents
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
        shutil.copytree(src, dst_dir, dirs_exist_ok=True)
        return ToolResult(True, "ok", {"restored_from": src})
    except Exception as e:
        return ToolResult(False, f"snapshot_restore error: {e}")

def env_info() -> ToolResult:
    try:
        return ToolResult(True, "ok", {
            "os": platform.system(),
            "os_release": platform.release(),
            "python": sys.version,
            "cwd": os.getcwd(),
            "path": os.environ.get("PATH","")[:2000]
        })
    except Exception as e:
        return ToolResult(False, f"env_info error: {e}")

def run_game_simulation(exe_path: str, metrics_path: str, args=None, log_dir: str = "workspace/logs", timeout: int = 120) -> ToolResult:
    """
    Executa o jogo Unity em modo Headless, escuta os logs em tempo real,
    grava-os num ficheiro e lê o metrics.json.
    """
    try:
        import subprocess, os, json
        from rich import print

        if not os.path.exists(exe_path):
            return ToolResult(False, f"Executable not found: {exe_path}")

        # Apaga métricas antigas para garantir que lemos as novas
        if os.path.exists(metrics_path):
            os.remove(metrics_path)

        cmd = [exe_path]
        if args:
            cmd.extend(args)

        print(f"\n[bold cyan]🚀 A lançar o Unity QA Bot...[/bold cyan]")
        print(f"[dim]A escutar a telemetria do motor em tempo real (Timeout: {timeout}s)...[/dim]\n")

        captured_output = []

        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8", errors="replace") as process:
            for line in process.stdout:
                clean_line = line.strip()
                if clean_line:
                    # Colorir os logs no Terminal para ser mais fácil ler
                    if "Exception" in clean_line or "Error" in clean_line or "Crash" in clean_line:
                        print(f"[bold red]  [UNITY][/bold red] {clean_line}")
                    elif "Warning" in clean_line:
                        print(f"[yellow]  [UNITY][/yellow] {clean_line}")
                    elif "BOT" in clean_line or "A iniciar Nível" in clean_line:
                        print(f"[bold green]  [BOT][/bold green] {clean_line}")
                    elif "[ROUND STATS]" in clean_line:
                        msg = clean_line.split("[ROUND STATS]")[-1].strip()
                        print(f"[bold cyan]  📊 {msg}[/bold cyan]")
                    else:
                        print(f"[dim]  [UNITY] {clean_line}[/dim]")

                    # Guardar a linha original na nossa lista
                    captured_output.append(clean_line)

            process.wait(timeout=timeout)

        stdout_str = "\n".join(captured_output)

        # 🚨 NOVO: GUARDAR O LOG COMPLETO NUM FICHEIRO FÍSICO!
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, "latest_simulation.log")

        with open(log_file_path, "w", encoding="utf-8") as f_log:
            f_log.write("=== LOG DA ÚLTIMA SIMULAÇÃO DO BOT ===\n\n")
            f_log.write(stdout_str)
            f_log.write("\n\n=== FIM DA SIMULAÇÃO ===")

        if not os.path.exists(metrics_path):
            return ToolResult(False, "Simulação terminou mas o metrics.json não foi gerado. O jogo crashou?", {"stdout": stdout_str})

        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        return ToolResult(True, "Simulation ok", {"metrics": metrics, "stdout": stdout_str})

    except subprocess.TimeoutExpired:
        process.kill()
        return ToolResult(False, "A Simulação demorou demasiado tempo e foi cancelada (Timeout).")
    except Exception as e:
        return ToolResult(False, f"Simulation error: {e}")