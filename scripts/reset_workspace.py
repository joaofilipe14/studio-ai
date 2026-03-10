from __future__ import annotations
import argparse
import os
import shutil
from pathlib import Path

# Agora limpamos tudo o que está DENTRO da pasta workspace/
SAFE_DEFAULTS = [
    "workspace/projects/game_001",
    "workspace/logs",
    "workspace/hall_of_fame",
    "workspace/releases"
]

def is_within(base: Path, target: Path) -> bool:
    try:
        base_r = base.resolve()
        targ_r = target.resolve()
        return str(targ_r).startswith(str(base_r) + os.sep)
    except Exception:
        return False

def safe_rmtree(repo_root: Path, rel_path: str) -> None:
    target = (repo_root / rel_path).resolve()
    if not is_within(repo_root, target):
        raise RuntimeError(f"Recusado (fora da raiz): {target}")
    if not target.exists():
        return
    if not target.is_dir():
        raise RuntimeError(f"Recusado (não é pasta): {target}")
    if target == repo_root:
        raise RuntimeError("Recusado (tentativa de apagar a raiz!).")

    print(f"[A apagar] {target}")
    shutil.rmtree(target, ignore_errors=False)

def main() -> int:
    parser = argparse.ArgumentParser(description="Limpeza do Chão de Fábrica.")
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    print("\n🧹 A INICIAR LIMPEZA DO WORKSPACE...\n")

    # Limpa as pastas voláteis dentro do workspace
    safe_rmtree(repo_root, "workspace/projects/game_001")
    safe_rmtree(repo_root, "workspace/logs")
    safe_rmtree(repo_root, "workspace/data")
    safe_rmtree(repo_root, "workspace/hall_of_fame")
    safe_rmtree(repo_root, "workspace/releases")

    print("\n✅ Reset concluído! O 'Chão de Fábrica' está limpo e pronto para nova simulação.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())