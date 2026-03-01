import base64
import json
import os
import requests
from io import BytesIO
from PIL import Image
from rembg import remove
from rich import print

# Configurações das APIs Locais
OLLAMA_URL = "http://localhost:11434/api/generate"
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# Determinar caminhos base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_SPRITES = os.path.join(BASE_DIR, "templates", "sprites")
TEMPLATE_TEXTURES = os.path.join(BASE_DIR, "templates", "textures")

def generate_character_prompt(genome: dict) -> str:
    """Pede ao Ollama para imaginar um personagem baseado na velocidade."""
    speed = genome.get("agent", {}).get("speed", 6.0)

    system_prompt = """You are an expert video game art director. Output ONLY comma-separated tags."""
    user_prompt = f"""Design a character sprite. Speed stat is {speed}. 
    If speed > 6: agile ninja/sci-fi runner. If speed < 5: heavy knight/golem.
    Technical tags: 'front view, symmetrical, standing still, flat colors, pure white background, pixel art, sharp edges'."""

    payload = {
        "model": "llama3",
        "prompt": f"{system_prompt}\n{user_prompt}",
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        return response.json().get("response", "").strip()
    except:
        return "pixel art character, standing, white background"

def save_and_process_image(img_b64, output_path, should_remove_bg=False):
    """Converte base64, processa (opcionalmente remove fundo) e guarda."""
    image_data = base64.b64decode(img_b64)
    image = Image.open(BytesIO(image_data))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if should_remove_bg:
        print(f"[yellow]✂️ Recortando fundo: {os.path.basename(output_path)}[/yellow]")
        image = remove(image)

    image.save(output_path, format="PNG")
    print(f"[bold green]✅ Guardado em:[/bold green] {output_path}")


def generate_art_asset(prompt, output_path, is_sprite=True):
    """Chama o Stable Diffusion usando a mesma LoRA para consistência."""
    print(f"[yellow]🎨 Gerando: {os.path.basename(output_path)}...[/yellow]")

    sd_payload = {
        "prompt": f"{prompt} <lora:128pixelartXL:1>",
        "negative_prompt": "photorealistic, realistic, 3d, shadows, gradients, messy, ugly, complex background",
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
        print(f"[red]Erro na API de Arte: {e}[/red]")

def generate_environment(genome: dict):
    """Gera texturas de chão e obstáculos baseadas no tema."""
    speed = genome.get("agent", {}).get("speed", 6.0)
    theme = "cyberpunk neon city" if speed > 7 else "medieval stone dungeon"

    # Gerar Chão (Seamless)
    floor_prompt = f"top-down view, {theme} floor tiles, seamless pattern, pixel art, flat colors"
    generate_art_asset(floor_prompt, os.path.join(TEMPLATE_TEXTURES, "FloorTexture.png"), is_sprite=False)

    # Gerar Obstáculo
    obs_prompt = f"top-down view, {theme} wall pillar, metal crate, pixel art, flat colors"
    generate_art_asset(obs_prompt, os.path.join(TEMPLATE_TEXTURES, "ObstacleTexture.png"), is_sprite=False)

if __name__ == "__main__":
    # Teste: Criar herói e ambiente para um ninja rápido
    test_genome = {"agent": {"speed": 9.0}}

    print("[magenta]🚀 Sessão de Arte Studio-AI Iniciada[/magenta]")

    # 1. Gerar Personagem
    char_prompt = generate_character_prompt(test_genome)
    generate_art_asset(char_prompt, os.path.join(TEMPLATE_SPRITES, "PlayerSprite.png"), is_sprite=True)

    # 2. Gerar Ambiente
    generate_environment(test_genome)