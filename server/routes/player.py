import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from shared.models import PlayerSaveModel

router = APIRouter(prefix="/player", tags=["Player"])

# 🎯 BALA DE PRATA: Descobre a raiz do projeto automaticamente (pasta 'core')
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Agora os caminhos são absolutos e nunca falham!
PLAYER_SAVE_PATH = BASE_DIR / "templates" / "json" / "player_save.json"
ROSTER_PATH = BASE_DIR / "templates" / "json" / "roster.json"

@router.get("/data", response_model=PlayerSaveModel)
def get_player_data():
    if not PLAYER_SAVE_PATH.exists():
        # Se falhar, ele agora avisa-te EXATAMENTE onde tentou procurar!
        raise HTTPException(status_code=404, detail=f"Save não encontrado em: {PLAYER_SAVE_PATH}")

    with open(PLAYER_SAVE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@router.post("/save")
def save_player_data(data: PlayerSaveModel):
    with open(PLAYER_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(data.dict(), f, indent=2)
    return {"status": "success"}

@router.get("/roster")
def get_roster():
    if not ROSTER_PATH.exists():
        return {"classes": []}
    with open(ROSTER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)