import json
import yaml
from pathlib import Path
from fastapi import APIRouter, HTTPException

# 🎯 Importamos a função diretamente do teu ficheiro central de base de dados!
from shared.db.evolution_logger import get_evolution_history

router = APIRouter(prefix="/performance", tags=["Performance"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

def get_db_path() -> str:
    """Lê o config.yaml e devolve o caminho absoluto para o evolution.db"""
    logs_dir = "workspace/logs"
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logs_dir = config.get("paths", {}).get("data", "workspace/logs")

    # Devolve o caminho como string porque o Pandas/SQLite prefere strings em vez de objetos Path
    return str(BASE_DIR / logs_dir / "evolution.db")

@router.get("/metrics")
def get_metrics():
    db_path = get_db_path()

    try:
        # 1. Vamos buscar o Pandas DataFrame usando a tua função nativa!
        df = get_evolution_history(db_path)

        if df.empty:
            return {"data": []}

        # 2. Limitamos aos últimos 50 registos para o React não "engasgar"
        df = df.head(50)

        # 3. Convertemos o DataFrame do Pandas para uma lista de dicionários Python
        records = df.to_dict(orient="records")

        data = []
        for entry in records:
            # 4. Traduzimos os nomes das colunas da BD para o formato que o React espera
            mapped_entry = {
                "id": entry["id"],
                "timestamp": entry["timestamp"],
                "level_id": entry["level_id"],
                "mode": entry["game_mode"], # Na BD é game_mode
                "win_rate": entry["win_rate"],
                "enemy_speed": entry["enemy_speed"],
                "is_human": bool(entry.get("is_human", 0)),
                "report": entry["ai_report"] # Na BD é ai_report
            }

            # 5. Extraímos a contagem de inimigos e obstáculos do JSON do genoma
            try:
                genome = json.loads(entry["genome_json"]) # Na BD é genome_json
                mapped_entry["enemy_count"] = genome.get("rules", {}).get("enemyCount", 0)
                mapped_entry["obstacles"] = genome.get("obstacles", {}).get("count", 0)
            except:
                mapped_entry["enemy_count"] = "N/A"
                mapped_entry["obstacles"] = "N/A"

            data.append(mapped_entry)

        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))