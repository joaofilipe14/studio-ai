import base64
import os
import json
import requests
from io import BytesIO
from PIL import Image
from rembg import remove
from rich import print

SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# Caminhos
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_SPRITES = os.path.join(BASE_DIR, "templates", "sprites")
TEMPLATE_TEXTURES = os.path.join(BASE_DIR, "templates", "textures")
ROSTER_PATH = os.path.join(BASE_DIR, "templates", "json", "roster.json")
RECIPES_PATH = os.path.join(BASE_DIR, "memory", "assets_recipes.json")

# O dicionário global que vai guardar TUDO
ASSET_RECIPES = {}

def load_all_recipes():
    global ASSET_RECIPES
    ASSET_RECIPES.clear()

    # Como o sync_assets.py agora trata de TUDO,
    # o nosso gerador só precisa de ler o ficheiro centralizado!
    if os.path.exists(RECIPES_PATH):
        try:
            with open(RECIPES_PATH, "r", encoding="utf-8") as f:
                base_recipes = json.load(f)
                ASSET_RECIPES.update(base_recipes)
        except Exception as e:
            print(f"[red]Erro ao ler {RECIPES_PATH}: {e}[/red]")
load_all_recipes()

def check_apis():
    try:
        requests.get("http://127.0.0.1:7860/", timeout=2)
    except requests.ConnectionError:
        raise ConnectionError("🎨 Servidor Stable Diffusion não encontrado!")

def save_and_process_image(img_b64, output_path, should_remove_bg=False):
    image_data = base64.b64decode(img_b64)
    image = Image.open(BytesIO(image_data))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if should_remove_bg:
        image = remove(image)

    image.save(output_path, format="PNG")

def generate_art_asset(prompt, output_path, is_sprite=True, negative_prompt=None):
    if not negative_prompt:
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
        raise RuntimeError(f"Falha ao gerar arte: {e}")

def generate_single_asset(theme: str, asset_key: str):
    check_apis()
    recipe = ASSET_RECIPES[asset_key]
    prompt = recipe["prompt"].format(theme=theme)
    neg_prompt = recipe.get("negative_prompt")

    print(f"[green]Prompt: {prompt}[/green]")
    if neg_prompt:
        print(f"[yellow]Negative Prompt: {neg_prompt}[/yellow]")

    out_dir = TEMPLATE_SPRITES if recipe["is_sprite"] else TEMPLATE_TEXTURES
    out_path = os.path.join(out_dir, recipe["file"])

    generate_art_asset(prompt, out_path, is_sprite=recipe["is_sprite"], negative_prompt=neg_prompt)

    return out_path

def generate_full_theme(genome: dict):
    check_apis()
    theme = genome.get("theme", "Cyberpunk Neon")
    for asset_key in ASSET_RECIPES.keys():
        generate_single_asset(theme, asset_key)