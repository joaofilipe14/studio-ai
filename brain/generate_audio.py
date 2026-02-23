import os
import scipy.io.wavfile
import torch
from transformers import pipeline

# Determina a raiz do projeto (assumindo que este script está dentro da pasta 'brain')
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MUSIC_DIR = os.path.join(BASE_DIR, "templates", "music")

def get_music_path(filename: str) -> str:
    """Garante que a pasta template/music existe e devolve o caminho completo."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    return os.path.join(MUSIC_DIR, filename)

def generate_game_music(prompt: str, filename: str = "synthwave_loop.wav", force_replace: bool = False) -> str:
    """
    Gera a música. Se force_replace for False, faz a validação e ignora se o ficheiro já existir.
    """
    filepath = get_music_path(filename)

    # VALIDAÇÃO: Se já existe e não estamos a forçar substituição, ignora.
    if os.path.exists(filepath) and not force_replace:
        print(f"⏭️ [Validação] A música já existe em: {filepath}")
        print("A ignorar a geração de áudio para poupar tempo. (Usa force_replace=True para criar uma nova)")
        return filepath

    print(f"🎵 A iniciar o pipeline MusicGen para criar: {filename}")

    # Deteta GPU ou CPU
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    # Só carrega o modelo pesado para a memória se realmente for gerar algo
    synthesiser = pipeline("text-to-audio", "facebook/musicgen-small", device=device)

    print(f"🎧 A compor nova música no dispositivo: {device.upper()}")
    print(f"Prompt: '{prompt}'")

    # max_new_tokens=512 gera cerca de 10 segundos de música
    music = synthesiser(prompt, forward_params={"max_new_tokens": 512})

    sampling_rate = music["sampling_rate"]
    audio_data = music["audio"][0].T

    scipy.io.wavfile.write(filepath, rate=sampling_rate, data=audio_data)
    print(f"✅ Sucesso! Nova faixa guardada em: {filepath}")
    return filepath

def replace_music(prompt: str, filename: str = "synthwave_loop.wav") -> str:
    """
    Método para substituir a música existente. Útil quando queres mudar o estilo ou apanhar uma melodia melhor.
    """
    print("🔄 A forçar a criação de uma NOVA música (substituindo a antiga)...")
    return generate_game_music(prompt, filename, force_replace=True)


if __name__ == "__main__":
    game_prompt = "A fast-paced retro 80s synthwave track, heavy bass, cybernetic arp, 120 bpm"

    # 1. Comportamento Padrão: Tenta gerar, mas valida se já existe.
    generate_game_music(game_prompt, "synthwave_loop.wav")

    # 2. Exemplo de Substituição:
    # Se quiseres forçar a IA a compor uma música 100% nova e apagar a anterior,
    # basta descomentares (tirar o #) da linha de baixo:
    # replace_music(game_prompt, "synthwave_loop.wav")