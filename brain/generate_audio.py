import os
import scipy.io.wavfile
import torch
import numpy as np
from transformers import pipeline


# Caminhos
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MUSIC_DIR = os.path.join(BASE_DIR, "templates", "music")

# Receitas de Áudio para a IA
AUDIO_RECIPES = {
    "Background Theme": {
        "file": "bg_theme.wav",
        "tokens": 1024,
        "suffix": "high-fidelity, ambient background music, clean, low volume mix"
    },
    "Collect Coin": {
        "file": "sfx_coin.wav",
        "tokens": 128,  # 🚨 Reduzido para ~1.5 - 2 segundos
        "suffix": "very short high-pitched chime, isolated, quick sparkle, no tail"
    },
    "Level Win": {
        "file": "sfx_win.wav",
        "tokens": 160,  # 🚨 Reduzido para ~2 segundos
        "suffix": "short triumphant orchestral burst, quick success jingle"
    },
    "Level Lose": {
        "file": "sfx_lose.wav",
        "tokens": 160,  # 🚨 Reduzido para ~2 segundos
        "suffix": "short game over synth hit, quick descending alert"
    }
}

def generate_audio_asset(theme_name: str, asset_key: str, force: bool = True):
    """Gera um asset específico baseado no tema e na receita."""
    recipe = AUDIO_RECIPES[asset_key]
    filepath = os.path.join(MUSIC_DIR, recipe["file"])

    if os.path.exists(filepath) and not force:
        return filepath

    os.makedirs(MUSIC_DIR, exist_ok=True)

    # Prompt Dinâmico: Tema + Descrição da Receita
    full_prompt = f"{theme_name} style, {recipe['suffix']}"

    print(f"🎵 A gerar {asset_key} ({theme_name})...")
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    synthesiser = pipeline("text-to-audio", "facebook/musicgen-medium", device=device)

    # Gerar (tokens menores para SFX para ser rápido)
    music = synthesiser(full_prompt, forward_params={"max_new_tokens": recipe["tokens"]})
    sampling_rate = music["sampling_rate"]
    audio_data = music["audio"][0].T

    # 🚨 NORMALIZAÇÃO DE ÁUDIO (Remove o "rache")
    # Impede que o som ultrapasse os limites e cause clipping
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val
    scipy.io.wavfile.write(filepath, rate=music["sampling_rate"], data=music["audio"][0].T)
    return filepath