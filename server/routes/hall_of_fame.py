import os
import json
import yaml
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/hall_of_fame", tags=["Hall of Fame"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

def get_hof_path() -> Path:
    hof_dir = "workspace/hall_of_fame"
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            hof_dir = config.get("paths", {}).get("hall_of_fame", "workspace/hall_of_fame")
    return BASE_DIR / hof_dir

@router.get("/compare")
def compare_campaigns():
    hof_path = get_hof_path()
    if not hof_path.exists():
        return {"data": []}

    campaigns = []

    # Lê todos os ficheiros de masterpiece
    for filename in os.listdir(hof_path):
        if filename.startswith("campaign_masterpiece_") and filename.endswith(".json"):
            filepath = hof_path / filename
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    genome_list = json.load(f)

                # Vamos calcular a curva de dificuldade da campanha
                level_stats = []
                total_difficulty = 0

                for level in genome_list:
                    enemies = level.get("rules", {}).get("enemyCount", 0)
                    speed = level.get("rules", {}).get("enemySpeed", 0.0)
                    obstacles = level.get("obstacles", {}).get("count", 0)
                    time_limit = level.get("rules", {}).get("timeLimit", 30.0)

                    # Fórmula de Dificuldade simples: (Ameaça) / (Tempo)
                    # Quanto mais inimigos e mais rápidos, com menos tempo, mais difícil é.
                    threat = (enemies * speed) + (obstacles * 0.1)
                    level_diff = float((threat / max(time_limit, 1.0)) * 100)

                    total_difficulty += level_diff
                    level_stats.append({
                        "level": f"Lvl {level.get('level_id', 0)}",
                        "difficulty": round(level_diff, 1),
                        "enemies": enemies,
                        "speed": round(speed, 1)
                    })

                campaigns.append({
                    "id": filename.replace("campaign_masterpiece_", "").replace(".json", ""),
                    "filename": filename,
                    "levels": level_stats,
                    "avg_difficulty": round(total_difficulty / len(genome_list), 1) if genome_list else 0
                })
            except Exception as e:
                print(f"Erro a ler {filename}: {e}")

    # Ordena da mais recente para a mais antiga
    campaigns.sort(key=lambda x: x["id"], reverse=True)
    return {"data": campaigns}