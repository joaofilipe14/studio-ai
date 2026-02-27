from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# Adicionamos as novas pastas aos defaults de segurança
SAFE_DEFAULTS = [
    "projects/game_001",
    "logs",
    "hall_of_fame",
    "releases"
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

def main() -> int:
    parser = argparse.ArgumentParser(description="Reset workspace safely (Fast Wipe).")
    parser.add_argument("--project", default="projects/game_001", help="Project folder to delete.")
    parser.add_argument("--delete-backups", action="store_true", help="Delete backups/ folder (DANGER).")
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()

    # Safety: must look like your repo root (has config.yaml)
    if not (repo_root / "config.yaml").exists():
        print("ERROR: config.yaml not found in current directory. Run from repo root (e.g., C:\\studio-ai).")
        return 2

    print(f"Repo root: {repo_root}")
    print("\n🧹 A INICIAR LIMPEZA TOTAL IMEDIATA...\n")

    # 1. Apagar pasta do Projeto (Desenvolvimento Unity e Build Atual)
    safe_rmtree(repo_root, args.project)

    # 2. Apagar pasta de Logs (Base de dados evolution.db, relatórios da IA)
    safe_rmtree(repo_root, "logs")

    # 3. Apagar Obras-Primas antigas
    safe_rmtree(repo_root, "hall_of_fame")

    # 4. Apagar Versões de Produção compiladas
    safe_rmtree(repo_root, "releases")

    # 5. Apagar backups (opcional)
    if args.delete_backups:
        safe_rmtree(repo_root, "backups")

    print("\n✅ Reset concluído com sucesso. Laboratório pronto para nova simulação!")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())