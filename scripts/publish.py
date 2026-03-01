import os
import shutil
from rich import print

def publish_game():
    print("[cyan]A iniciar o Pipeline de Release (Studio-AI - Fase 4)...[/cyan]")

    builds_dir = os.path.join("projects", "game_001", "Builds")
    release_dir = os.path.join("releases", "game_prod")

    if not os.path.exists(builds_dir):
        print("[red]Erro: Pasta de Builds não encontrada. Corre o Orquestrador primeiro.[/red]")
        return

    print(f"[white]A limpar a versão de produção anterior em {release_dir}...[/white]")
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir, exist_ok=True)

    print(f"[white]A empacotar o executável e dados para a Produção...[/white]")

    # 1. Copiar todos os ficheiros compilados do Unity (O .exe, os .dll, e a pasta _Data)
    for item in os.listdir(builds_dir):
        s = os.path.join(builds_dir, item)
        d = os.path.join(release_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # 2. Garantir que os 3 novos JSONs estruturais vão junto
    json_files = ["level_genome.json", "roster.json", "player_save.json"]
    for j_file in json_files:
        # Primeiro tenta copiar da raiz do projeto (onde estão sempre atualizados)
        src = os.path.join(".", j_file)
        dest = os.path.join(release_dir, j_file)

        # Se não estiverem na raiz (por exemplo, na primeiríssima execução), vai aos templates
        if not os.path.exists(src):
            src = os.path.join("templates", "unity", j_file)

        if os.path.exists(src):
            shutil.copy2(src, dest)
            print(f"[green]✓ {j_file} empacotado.[/green]")
        else:
            print(f"[yellow]Aviso: Não encontrei o {j_file} para incluir na release.[/yellow]")

    print(f"\n[bold green]🎉 Release de Produção concluída com sucesso![/bold green]")
    print(f"O teu jogo final está na pasta: {os.path.abspath(release_dir)}\n")

if __name__ == "__main__":
    publish_game()