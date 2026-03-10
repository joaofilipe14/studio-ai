import os
import scipy.io.wavfile
import torch
import numpy as np
from transformers import pipeline

# Sobe dois níveis para chegar à raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MUSIC_DIR = os.path.join(BASE_DIR, "templates", "music")

AUDIO_RECIPES = {
    "Background Theme": {
        "file": "bg_theme.wav",
        "tokens": 1024,
        "suffix": "high-fidelity, ambient background music, clean, low volume mix"
    },
    "Collect Coin": {
        "file": "sfx_coin.wav",
        "tokens": 128,
        "suffix": "very short high-pitched chime, isolated, quick sparkle, no tail"
    },
    "Level Win": {
        "file": "sfx_win.wav",
        "tokens": 160,
        "suffix": "short triumphant orchestral burst, quick success jingle"
    },
    "Level Lose": {
        "file": "sfx_lose.wav",
        "tokens": 160,
        "suffix": "short game over synth hit, quick descending alert"
    }
}

def generate_audio_asset(theme_name: str, asset_key: str, force: bool = True):
    recipe = AUDIO_RECIPES[asset_key]
    filepath = os.path.join(MUSIC_DIR, recipe["file"])

    if os.path.exists(filepath) and not force:
        return filepath

    os.makedirs(MUSIC_DIR, exist_ok=True)
    full_prompt = f"{theme_name} style, {recipe['suffix']}"

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    synthesiser = pipeline("text-to-audio", "facebook/musicgen-medium", device=device)

    music = synthesiser(full_prompt, forward_params={"max_new_tokens": recipe["tokens"]})
    sampling_rate = music["sampling_rate"]
    audio_data = music["audio"][0].T

    # NORMALIZAÇÃO DE ÁUDIO
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val

    scipy.io.wavfile.write(filepath, rate=sampling_rate, data=audio_data)
    return filepath