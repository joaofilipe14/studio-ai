import base64
import json
import os
import requests
from io import BytesIO
from PIL import Image
from rembg import remove
from rich import print

# Configurações das APIs Locais
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# Determinar caminhos base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_SPRITES = os.path.join(BASE_DIR, "templates", "sprites")
TEMPLATE_TEXTURES = os.path.join(BASE_DIR, "templates", "textures")

# 🚨 RECEITAS ESTritas (Para forçar vista Top-Down e Pixel Art puro)
ASSET_RECIPES = {
    "Player": {"file": "PlayerSprite.png", "is_sprite": True, "prompt": "pixel art sprite, {theme} main hero character, top-down perspective, full body, isolated on pure white background, flat colors"},
    "Enemy": {"file": "EnemySprite.png", "is_sprite": True, "prompt": "pixel art sprite, {theme} scary enemy monster, top-down perspective, full body, isolated on pure white background, flat colors"},
    "Floor": {"file": "FloorTexture.png", "is_sprite": False, "prompt": "pixel art texture, {theme} floor tile, strictly top-down view, seamless pattern, flat 2d surface, no perspective"},
    "Wall": {"file": "ObstacleTexture.png", "is_sprite": False, "prompt": "pixel art texture, {theme} solid metal wall crate, strictly top-down view, flat 2d, no perspective"},
    "Goal": {"file": "GoalTexture.png", "is_sprite": False, "prompt": "pixel art texture, {theme} glowing exit teleport pad, strictly top-down view, flat 2d, centered"},
    "Collectible": {"file": "CollectibleTexture.png", "is_sprite": False, "prompt": "pixel art texture, {theme} shiny valuable coin item, strictly top-down view, centered, isolated on solid background"},
    "Trap": {"file": "TrapTexture.png", "is_sprite": False, "prompt": "pixel art texture, {theme} dangerous floor spikes trap, strictly top-down view, flat 2d, no perspective"},
    "PowerUp": {"file": "PowerUpTexture.png", "is_sprite": False, "prompt": "pixel art texture, {theme} glowing energy battery potion, strictly top-down view, centered, flat 2d"}
}

def check_apis():
    try:
        requests.get("http://127.0.0.1:7860/", timeout=2)
    except requests.ConnectionError:
        raise ConnectionError("🎨 Servidor Stable Diffusion não encontrado! Garante que o WebUI está a correr com --api.")

def save_and_process_image(img_b64, output_path, should_remove_bg=False):
    image_data = base64.b64decode(img_b64)
    image = Image.open(BytesIO(image_data))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if should_remove_bg:
        print(f"[yellow]✂️ Recortando fundo: {os.path.basename(output_path)}[/yellow]")
        image = remove(image)

    image.save(output_path, format="PNG")
    print(f"[bold green]✅ Guardado em:[/bold green] {output_path}")

def generate_art_asset(prompt, output_path, is_sprite=True):
    print(f"[yellow]🎨 A pintar: {os.path.basename(output_path)}...[/yellow]")

    # 🚨 NEGATIVE PROMPT ESTrito (Proíbe 3D, isometria e paisagens)
    negative_prompt = "photorealistic, realistic, 3d, isometric, perspective, landscape, scenery, shadows, gradients, messy, ugly, complex background, text, watermark"

    sd_payload = {
        "prompt": f"{prompt} <lora:128pixelartXL:1>",
        "negative_prompt": negative_prompt,
        "steps": 25,
        "cfg_scale": 7.5,
        "width": 1024,
        "height": 1024,
        "sampler_name": "Euler a",
        "override_settings": {
            "sd_model_checkpoint": "realvisxlV50_v50LightningBakedvae.safetensors"
        }
    }

    try:
        response = requests.post(SD_API_URL, json=sd_payload)
        response.raise_for_status()
        img_b64 = response.json()["images"][0]
        save_and_process_image(img_b64, output_path, should_remove_bg=is_sprite)
    except Exception as e:
        raise RuntimeError(f"Falha ao gerar {os.path.basename(output_path)}: {e}")

def generate_single_asset(theme: str, asset_key: str):
    """Gera apenas um asset específico a partir das receitas."""
    check_apis()
    recipe = ASSET_RECIPES[asset_key]
    prompt = recipe["prompt"].format(theme=theme)

    out_dir = TEMPLATE_SPRITES if recipe["is_sprite"] else TEMPLATE_TEXTURES
    out_path = os.path.join(out_dir, recipe["file"])

    generate_art_asset(prompt, out_path, is_sprite=recipe["is_sprite"])
    return out_path

def generate_full_theme(genome: dict):
    """Gera TODOS os assets do jogo baseados no tema atual."""
    check_apis()
    theme = genome.get("theme", "Cyberpunk Neon")
    print(f"\n[bold magenta]🚀 A iniciar criação do Pacote de Arte: {theme}[/bold magenta]")

    for asset_key in ASSET_RECIPES.keys():
        generate_single_asset(theme, asset_key)

    print("\n[bold green]🎉 Pacote de Arte Completo Gerado com Sucesso![/bold green]")