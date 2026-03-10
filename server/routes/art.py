from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Importamos o teu script de IA de arte
from services.art_studio.generator import ASSET_RECIPES, generate_single_asset, generate_full_theme

router = APIRouter(prefix="/art", tags=["Art"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SPRITES_DIR = BASE_DIR / "templates" / "sprites"
TEXTURES_DIR = BASE_DIR / "templates" / "textures"

class ArtGenerateRequest(BaseModel):
    theme: str = "Cyberpunk Neon"
    asset_key: str

@router.get("/list")
def list_art():
    """Lista todos os assets disponíveis nas tuas receitas."""
    assets = []
    for key, recipe in ASSET_RECIPES.items():
        folder = SPRITES_DIR if recipe["is_sprite"] else TEXTURES_DIR
        filepath = folder / recipe["file"]
        status = "Pronto" if filepath.exists() else "Pendente"

        assets.append({
            "id": key,
            "name": key,
            "filename": recipe["file"],
            "is_sprite": recipe["is_sprite"],
            "status": status
        })
    return {"assets": assets}

@router.get("/image/{type}/{filename}")
def get_image(type: str, filename: str):
    """Serve a imagem PNG para o browser renderizar."""
    folder = SPRITES_DIR if type == "sprite" else TEXTURES_DIR
    filepath = folder / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    return FileResponse(filepath, media_type="image/png")

@router.post("/generate")
def generate_art(req: ArtGenerateRequest):
    """Manda o comando para o Stable Diffusion."""
    try:
        if req.asset_key == "all":
            # 🎯 Agora usamos a tua função nativa e elegante!
            generate_full_theme({"theme": req.theme})
            return {"status": "success", "message": "Todas as artes geradas!"}

        # Gera apenas um
        generate_single_asset(req.theme, req.asset_key)
        return {"status": "success", "message": f"{req.asset_key} gerado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))