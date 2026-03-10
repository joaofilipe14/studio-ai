import os
import shutil
import yaml
from rich import print

def load_yaml(path: str):
    """Carrega as configurações do projeto."""
    if not os.path.exists(path):
        # Se for chamado de dentro da pasta scripts, recua um nível
        alt_path = os.path.join("..", path)
        path = alt_path if os.path.exists(alt_path) else path

    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def publish_game():
    print("[cyan]A iniciar o Pipeline de Release (Studio-AI - Fase 4)...[/cyan]")

    # 0. CARREGAR CONFIGURAÇÃO DINÂMICA
    config = load_yaml("config.yaml")
    paths = config.get("paths", {})

    # Lemos os caminhos configurados
    projects_root = paths.get("projects", "workspace/projects")
    # 🎯 Agora a release vai para dentro do workspace!
    releases_root = paths.get("releases", "workspace/releases")

    pn = "game_001"
    builds_dir = os.path.join(projects_root, pn, "Builds")
    release_dir = os.path.join(releases_root, "game_prod") # 🎯 Caminho atualizado

    if not os.path.exists(builds_dir):
        print(f"[red]Erro: Pasta de Builds não encontrada em {builds_dir}.[/red]")
        return

    print(f"[white]A limpar a versão de produção anterior em {release_dir}...[/white]")
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir, exist_ok=True)

    print(f"[white]A empacotar o executável e dados para a Produção...[/white]")

    # 1. Copiar todos os ficheiros compilados do Unity
    for item in os.listdir(builds_dir):
        s = os.path.join(builds_dir, item)
        d = os.path.join(release_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # 2. Garantir que os ficheiros JSON estruturais vão junto
    # Agora procuramos nos novos locais centralizados: templates/json
    json_files = ["level_genome.json", "roster.json", "player_save.json"]
    for j_file in json_files:
        # 🎯 Ordem de procura:
        # 1. Memória de templates (onde a IA guarda as evoluções manuais)
        # 2. Pasta raiz
        # 3. Pasta de templates originais do Unity
        sources = [
            os.path.join("templates", "json", j_file),
            os.path.join(".", j_file),
            os.path.join("templates", "unity", j_file)
        ]

        copied = False
        for src in sources:
            if os.path.exists(src):
                dest = os.path.join(release_dir, j_file)
                shutil.copy2(src, dest)
                print(f"[green]✓ {j_file} empacotado (via {src}).[/green]")
                copied = True
                break

        if not copied:
            print(f"[yellow]Aviso: Não encontrei o {j_file} em nenhum diretório de origem.[/yellow]")

    print(f"\n[bold green]🎉 Release de Produção concluída com sucesso![/bold green]")
    print(f"O teu jogo final está na pasta: {os.path.abspath(release_dir)}\n")