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

def generate_character_prompt(genome: dict) -> str:
    """Pede ao Ollama para imaginar um personagem baseado nos status do jogo."""
    speed = genome.get("agent", {}).get("speed", 6.0)

    # Prompt simples para o Ollama
    system_prompt = """You are an expert video game art director for a voxel-based 3D game. 
    Your job is to write a highly detailed Stable Diffusion prompt. 
    Output ONLY a comma-separated list of tags. No intro, no sentences, no markdown."""

    # Adicionamos lógica para o LLM escolher um "tema" com base na velocidade!
    user_prompt = f"""Design a character sprite for a maze runner game. 
    The character's speed stat is {speed} (If speed is high > 6, make them look agile like a ninja, rogue, or fast sci-fi runner. If speed is low < 5, make them look heavy like a knight, golem, or tank). 
    
    You MUST include these exact technical tags for the voxelizer to work:
    'front view, symmetrical, standing still, flat colors, strictly no gradients, pure white background, minimalist 8-bit pixel art, sharp edges'
    
    Describe the character's visual details now. Return ONLY the comma-separated tags."""

    payload = {
        "model": "llama3", # Substitui pelo modelo que usas (ex: phi3, mistral)
        "prompt": f"{system_prompt}\n{user_prompt}",
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        art_prompt = response.json().get("response", "").strip()
        print(f"[cyan]🎨 Ollama imaginou:[/cyan] {art_prompt}")
        return art_prompt
    except Exception as e:
        print(f"[red]Erro ao falar com o Ollama: {e}[/red]")
        return "pixel art character, top down view, simple, white background"

def generate_and_cut_sprite(prompt: str, output_path: str):
    """Pede ao Stable Diffusion para desenhar e usa o rembg para cortar o fundo."""
    print("[yellow]A desenhar o sprite no Stable Diffusion...[/yellow]")

    # Payload para o AUTOMATIC1111
    sd_payload = {
        "prompt": prompt+" <lora:128pixelartXL:1>",
        "negative_prompt": "photorealistic, realistic, 3d render, shadows, gradients, anti-aliasing, messy, ugly, complex background",
        "steps": 25,
        "cfg_scale": 7.5,
        "width": 1024,   # OBRIGATÓRIO PARA SDXL!
        "height": 1024,  # OBRIGATÓRIO PARA SDXL!
        "sampler_name": "Euler a",

        # Esta linha obriga a API a trocar para o modelo Pixel Art antes de desenhar
        "override_settings": {
            "sd_model_checkpoint": "realvisxlV50_v50LightningBakedvae.safetensors" # Ex: "pixelArtXL_v10.safetensors"
        }
    }

    try:
        # 1. Gerar Imagem
        response = requests.post(SD_API_URL, json=sd_payload)
        response.raise_for_status()
        img_b64 = response.json()["images"][0]

        # Converter Base64 para Imagem do Pillow
        image_data = base64.b64decode(img_b64)
        input_image = Image.open(BytesIO(image_data))

        print("[yellow]A recortar o fundo (rembg)...[/yellow]")
        # 2. Cortar Fundo
        output_image = remove(input_image)

        # 3. Guardar no Unity
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        output_image.save(output_path, format="PNG")
        print(f"[bold green]✅ Sprite guardado com sucesso em:[/bold green] {output_path}")

    except Exception as e:
        print(f"[red]Erro na geração de arte: {e}[/red]")

if __name__ == "__main__":
    # Teste rápido de arte!
    teste_genome = {"agent": {"speed": 9.0}} # Personagem rápido

    # Caminho onde o Unity vai ler a imagem dinamicamente (Resources)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sprite_dir = os.path.join(base_dir, "templates", "sprites")
    os.makedirs(sprite_dir, exist_ok=True)
    sprite_path = os.path.join(sprite_dir, "PlayerSprite.png")

    print("[magenta]A iniciar a sessão de Arte...[/magenta]")
    art_prompt = generate_character_prompt(teste_genome)
    generate_and_cut_sprite(art_prompt, sprite_path)