import os
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

# --- IMPORTAÇÕES DAS TUAS LÓGICAS ---
from brain.game_director import evolve_bot_genome, evolve_human_genome
from brain.marketing_agent import (
    generate_weekly_marketing_plan,
    load_marketing_plan,
    save_marketing_plan,
    MARKETING_FILE
)
from brain.art_director import generate_full_theme, ASSET_RECIPES, generate_single_asset
from brain.generate_audio import generate_audio_asset, AUDIO_RECIPES

app = FastAPI(
    title="Studio-AI Central API",
    description="Espinha dorsal do Studio-AI: Gere a evolução do jogo, marketing e assets.",
    version="1.1.0"
)

# --- MODELOS DE DADOS (Pydantic) ---
class GameEvolutionRequest(BaseModel):
    config: dict          # Config do Ollama (host, model)
    metrics: dict         # Métricas do Unity (level_reports)
    current_genome: dict  # Genoma atual para evoluir
    is_human: bool = False

class MarketingReview(BaseModel):
    index: int
    text: str
    reviewed: bool

# --- ENDPOINTS DE STATUS ---
@app.get("/")
def health_check():
    return {"status": "Studio-AI API Online", "memory_path": MARKETING_FILE}

# --- 🧠 ENDPOINT: GAME DIRECTOR (Unity) ---
@app.post("/director/evolve")
async def evolve_level(request: GameEvolutionRequest):
    """Aplica a lógica de 'Mão de Ferro' e psicologia de jogo para criar o próximo nível."""
    try:
        if request.is_human:
            result = evolve_human_genome(request.config, request.metrics, request.current_genome)
        else:
            result = evolve_bot_genome(request.config, request.metrics, request.current_genome)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na Evolução: {str(e)}")

# --- 🚀 ENDPOINTS: MARKETING HUB (Dashboard) ---
@app.get("/marketing/plan")
def get_marketing():
    """Lê o plano de marketing da pasta memory."""
    plan = load_marketing_plan()
    return {"status": "success", "plan": plan if plan else []}

@app.post("/marketing/generate")
async def generate_marketing(theme: str):
    """Gera novos posts baseados no histórico de evolução."""
    db_path = os.path.join("logs", "evolution.db")
    plan = generate_weekly_marketing_plan(db_path, theme)
    return {"status": "generated", "plan": plan}

@app.put("/marketing/review")
def review_post(review: MarketingReview):
    """Atualiza o estado de aprovação e o texto de um post específico no JSON."""
    plan = load_marketing_plan()
    if not plan or review.index >= len(plan):
        raise HTTPException(status_code=404, detail="Post não encontrado")

    plan[review.index]["texto"] = review.text
    plan[review.index]["reviewed"] = review.reviewed
    save_marketing_plan(plan)
    return {"status": "updated"}

# --- 🎨 ENDPOINTS: ESTÚDIO DE ARTE ---
@app.post("/assets/art/theme")
async def generate_theme_assets(theme_name: str):
    """Gera o pacote completo de texturas e sprites via Stable Diffusion."""
    try:
        generate_full_theme({"theme": theme_name})
        return {"status": "success", "theme": theme_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assets/art/single")
async def generate_asset(theme_name: str, asset_key: str):
    """Regenera um único elemento visual (ex: PlayerSprite)."""
    if asset_key not in ASSET_RECIPES:
        raise HTTPException(status_code=400, detail="Asset inválido")
    generate_single_asset(theme_name, asset_key)
    return {"status": "success", "asset": asset_key}

# --- 🎵 ENDPOINTS: SONOPLASTIA ---
@app.post("/assets/audio/generate")
async def generate_audio(asset_key: str, theme: str = "Default"):
    """Gera efeitos sonoros curtos (máx 2s) para o jogo."""
    if asset_key not in AUDIO_RECIPES:
        raise HTTPException(status_code=400, detail="Receita de áudio não encontrada")
    generate_audio_asset(theme, asset_key)
    return {"status": "success", "audio": asset_key}