import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Importamos o teu sintetizador e as receitas do ficheiro synth.py
from services.sonic_lab.synth import generate_audio_asset, AUDIO_RECIPES

router = APIRouter(prefix="/audio", tags=["Audio"])

# Encontrar a raiz do projeto (pasta core)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MUSIC_DIR = BASE_DIR / "templates" / "music"

class GenerateRequest(BaseModel):
    theme_name: str = "Cyberpunk Neon"
    asset_key: str  # Pode ser "Background Theme", "Collect Coin", etc. ou "all"

@router.get("/list")
def list_audio():
    """Devolve a lista de áudios e diz se já existem no disco ou não."""
    tracks = []
    id_counter = 1

    for key, recipe in AUDIO_RECIPES.items():
        filepath = MUSIC_DIR / recipe["file"]
        status = "Pronto" if filepath.exists() else "Pendente"
        is_bgm = "Theme" in key

        tracks.append({
            "id": id_counter,
            "name": key,
            "filename": recipe["file"],
            "type": "BGM" if is_bgm else "SFX",
            "status": status
        })
        id_counter += 1

    return {"tracks": tracks}

@router.get("/play/{filename}")
def play_audio(filename: str):
    """Serve o ficheiro .wav diretamente para o HTML/React reproduzir!"""
    filepath = MUSIC_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Ficheiro de áudio não encontrado.")
    return FileResponse(filepath, media_type="audio/wav")

@router.post("/generate")
def generate_audio(req: GenerateRequest):
    """Manda a IA (MusicGen) gerar o som."""
    try:
        if req.asset_key == "all":
            for key in AUDIO_RECIPES.keys():
                generate_audio_asset(req.theme_name, key, force=True)
            return {"status": "success", "message": "Todos os áudios foram gerados!"}

        if req.asset_key not in AUDIO_RECIPES:
            raise HTTPException(status_code=400, detail="Asset key inválida.")

        generate_audio_asset(req.theme_name, req.asset_key, force=True)
        return {"status": "success", "message": f"{req.asset_key} gerado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))