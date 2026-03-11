import os
import json
import yaml
import sqlite3
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

def get_paths():
    """Lê as pastas dinâmicas do config.yaml"""
    paths = {"releases": "workspace/releases", "logs": "workspace/logs", "hof": "workspace/hall_of_fame"}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            paths.update(config.get("paths", {}))

    return {
        "releases": BASE_DIR / paths["releases"],
        "logs": BASE_DIR / paths["logs"],
        "hof": BASE_DIR / paths["hof"] # hof = Hall of Fame
    }

@router.get("/summary")
def get_summary():
    paths = get_paths()

    # 1. Dados do Jogador (A ler da Release de Produção)
    player_data = {"name": "Desconhecido", "coins": 0, "level": 1, "wins": 0}
    player_file = paths["releases"] / "game_prod" / "player_save.json"

    if player_file.exists():
        try:
            with open(player_file, "r", encoding="utf-8") as f:
                save = json.load(f)
                player_data["name"] = save.get("playerName", "Director")
                player_data["coins"] = save.get("wallet", {}).get("totalCoins", 0)
                player_data["level"] = save.get("currentCampaignLevel", 1)
                player_data["wins"] = save.get("stats", {}).get("totalWins", 0)
        except Exception as e:
            print(f"Erro ao ler player_save: {e}")

    # 2. Dados da Evolução (A ler do SQLite)
    evo_data = {"total_generations": 0, "latest_level": 1}
    db_path = paths["logs"] / "evolution.db"

    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Conta o total de simulações feitas
            cursor.execute("SELECT COUNT(*) FROM evolution")
            evo_data["total_generations"] = cursor.fetchone()[0]

            # Vê qual foi o último nível em que a IA esteve a trabalhar
            cursor.execute("SELECT level_id FROM evolution ORDER BY id DESC LIMIT 1")
            last_row = cursor.fetchone()
            if last_row:
                evo_data["latest_level"] = last_row[0]

            conn.close()
        except Exception as e:
            print(f"Erro ao ler DB: {e}")

    # 3. Dados do Hall of Fame
    hof_count = 0
    if paths["hof"].exists():
        hof_count = len([f for f in os.listdir(paths["hof"]) if f.startswith("campaign_masterpiece_")])

    return {
        "player": player_data,
        "evolution": evo_data,
        "hall_of_fame": hof_count
    }