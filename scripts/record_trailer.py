import os
import subprocess
import yaml
import glob
from PIL import Image
from rich import print

def load_yaml(path: str):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def record_and_compile():
    print("[cyan]🎬 Bem-vindo ao Studio-AI: Realizador Automático[/cyan]")

    # 1. Caminhos Absolutos e Robustos
    # __file__ garante que sabemos sempre onde estamos, não importa de onde corras o script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(script_dir, ".."))

    config_path = os.path.join(base_dir, "config.yaml")
    config = load_yaml(config_path)

    projects_root = config.get("paths", {}).get("projects", "workspace/projects")
    builds_dir = os.path.join(base_dir, projects_root, "game_001", "Builds")

    # 🚨 LÓGICA CAÇA-EXECUTÁVEIS 🚨
    # Procura qualquer .exe na pasta de Builds e ignora o CrashHandler do Unity
    exe_candidates = glob.glob(os.path.join(builds_dir, "*.exe"))
    valid_exes = [exe for exe in exe_candidates if "CrashHandler" not in exe]

    if not valid_exes:
        print(f"[red]❌ ERRO: Não encontrei nenhum executável (.exe) na pasta:[/red]\n{builds_dir}")
        print("[yellow]💡 Dica: Já fizeste o Build (File -> Build Settings) do teu jogo no Unity para esta pasta?[/yellow]")
        return

    exe_path = valid_exes[0] # Pega no primeiro executável válido que encontrar
    print(f"[white]🎮 Executável encontrado: {os.path.basename(exe_path)}[/white]")

    marketing_dir = os.path.join(base_dir, "workspace", "marketing")
    frames_dir = os.path.join(marketing_dir, "trailer_frames")

    os.makedirs(frames_dir, exist_ok=True)

    # 2. Limpar frames antigos
    print("[yellow]A limpar o estúdio de gravação...[/yellow]")
    old_frames = glob.glob(os.path.join(frames_dir, "*.png"))
    for f in old_frames:
        os.remove(f)

    # 3. Mandar o Unity gravar o nível sozinho!
    print(f"[green]A lançar o motor de jogo no Modo Trailer...[/green]")
    cmd = [
        exe_path,
        "-trailerMode",
        "-trailerFolder", os.path.abspath(frames_dir),  # 🚨 NOVO: Dizemos ao Unity exatamente onde gravar
        "-screen-width", "1280",
        "-screen-height", "720",
        "-windowed"
    ]

    exe_dir = os.path.dirname(exe_path)

    try:
        subprocess.run(cmd, cwd=exe_dir, check=True)
    except Exception as e:
        print(f"[red]❌ Falha ao tentar abrir o Unity: {e}[/red]")
        return

    print("[green]✓ Gravação terminada! O Unity fechou as portas.[/green]")

    # 4. Pegar nos ficheiros PNG e compilar um GIF
    frames = sorted(glob.glob(os.path.join(frames_dir, "frame_*.png")))

    if not frames:
        print("[red]❌ Erro: O Unity não gerou nenhum frame. O TrailerDirector.cs está no teu GameManager?[/red]")
        return

    print(f"[yellow]A compilar {len(frames)} frames num Trailer Animado...[/yellow]")

    images = []
    for filename in frames:
        img = Image.open(filename)
        images.append(img.copy())
        img.close()

    output_path = os.path.join(marketing_dir, "latest_trailer.gif")

    # Guarda como GIF animado
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        optimize=True,
        duration=33,
        loop=0
    )

    print(f"\n[bold green]🎉 Trailer compilado com sucesso![/bold green]")
    print(f"Podes ver a tua obra-prima em:\n[cyan]{output_path}[/cyan]\n")

if __name__ == "__main__":
    record_and_compile()