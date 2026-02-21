from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


SAFE_DEFAULTS = [
    "projects/game_001",
    "logs",
]


def is_within(base: Path, target: Path) -> bool:
    """Return True if target is within base (after resolving)."""
    try:
        base_r = base.resolve()
        targ_r = target.resolve()
        return str(targ_r).startswith(str(base_r) + os.sep)
    except Exception:
        return False


def safe_rmtree(repo_root: Path, rel_path: str) -> None:
    """Remove a directory under repo_root safely."""
    target = (repo_root / rel_path).resolve()

    # Must be inside repo root
    if not is_within(repo_root, target):
        raise RuntimeError(f"Refusing to delete outside repo root: {target}")

    # Must exist and be a directory
    if not target.exists():
        print(f"[skip] not found: {target}")
        return
    if not target.is_dir():
        raise RuntimeError(f"Refusing to delete non-directory: {target}")

    # Guard against deleting repo root itself
    if target == repo_root:
        raise RuntimeError("Refusing to delete repo root.")

    print(f"[delete] {target}")
    shutil.rmtree(target, ignore_errors=False)


def delete_unity_logs(repo_root: Path, pattern: str = "unity-") -> None:
    logs_dir = (repo_root / "logs").resolve()
    if not logs_dir.exists():
        return
    if not is_within(repo_root, logs_dir):
        raise RuntimeError("logs dir is outside repo root?")

    deleted = 0
    for p in logs_dir.glob("*.log"):
        if pattern in p.name:
            print(f"[delete] {p}")
            p.unlink(missing_ok=True)
            deleted += 1
    if deleted == 0:
        print("[skip] no unity logs matched")


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset workspace safely (Unity projects/logs).")
    parser.add_argument("--project", default="projects/game_001", help="Project folder to delete (relative to repo).")
    parser.add_argument("--delete-logs", action="store_true", help="Delete Unity logs in logs/ (unity-*.log).")
    parser.add_argument("--delete-backups", action="store_true", help="Delete backups/ folder (DANGER).")
    parser.add_argument("--yes", action="store_true", help="Do not prompt.")
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()

    # Safety: must look like your repo root (has config.yaml)
    if not (repo_root / "config.yaml").exists():
        print("ERROR: config.yaml not found in current directory. Run from repo root (e.g., C:\\studio-ai).")
        return 2

    print(f"Repo root: {repo_root}")
    print(f"Will delete: {args.project}")
    if args.delete_logs:
        print("Will delete: logs/unity-*.log")
    if args.delete_backups:
        print("Will delete: backups/ (DANGER)")

    if not args.yes:
        ans = input("Type 'RESET' to continue: ").strip()
        if ans != "RESET":
            print("Aborted.")
            return 1

    # Delete project folder
    safe_rmtree(repo_root, args.project)

    # Delete unity logs
    if args.delete_logs:
        delete_unity_logs(repo_root, pattern="unity-")
        logs_folder = repo_root / "logs"
        if logs_folder.exists() and not any(logs_folder.iterdir()):
            # Se a pasta estiver vazia após apagar os logs, removemos a pasta
            safe_rmtree(repo_root, "logs")
        elif logs_folder.exists():
            # Forçar a remoção da pasta e tudo lá dentro
            safe_rmtree(repo_root, "logs")

    # Delete backups (optional)
    if args.delete_backups:
        safe_rmtree(repo_root, "backups")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())