import subprocess
import xml.etree.ElementTree as ET
import os
import yaml
from rich import print

# 🚨 IMPORTA O TEU ORQUESTRADOR!
from runner import main_runner

def run_unity_tests():
    print("[cyan]A iniciar Unity Test Runner em background...[/cyan]")

    # 1. Carrega as tuas configurações
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"[red]Erro crítico: Ficheiro {config_path} não encontrado![/red]")
        return False

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 🚨 A CORREÇÃO ESTÁ AQUI: Versão correta do Unity e caminho dinâmico para a pasta game_001
    unity_exe = config.get("paths", {}).get("unity_path", "C:/Program Files/Unity/Hub/Editor/6000.3.9f1/Editor/Unity.exe")
    projects_dir = config.get("paths", {}).get("projects", "workspace/projects")
    project_path = os.path.abspath(os.path.join(projects_dir, "game_001"))

    # 🚨 NOVO: VERIFICA SE O PROJETO EXISTE (Verificamos a pasta Assets)
    assets_path = os.path.join(project_path, "Assets")

    if not os.path.exists(assets_path):
        print(f"[yellow]Aviso: Projeto Unity não encontrado em {project_path}.[/yellow]")
        print("[cyan]A IA vai gerar e montar o projeto primeiro (Runner)... Pode demorar um pouco![/cyan]")

        # Chama o orquestrador para construir o projeto do zero
        main_runner()

        # Verifica novamente se o projeto foi criado com sucesso
        if not os.path.exists(assets_path):
            print("[red]Erro crítico: Falha ao criar o projeto. Não é possível correr os testes Unitários.[/red]")
            return False
        else:
            print("[green]Projeto Unity confirmado! A arrancar com os testes...[/green]")

    results_xml = os.path.abspath("test_results.xml")
    log_file = os.path.abspath("test_log.txt")

    # 2. O Comando Mágico do Unity para correr testes sem abrir o Editor
    cmd = [
        unity_exe,
        "-batchmode",
        "-projectPath", project_path,
        "-runTests",
        "-testPlatform", "EditMode",
        "-testResults", results_xml,
        "-logFile", log_file
    ]

    # Executa o Unity e espera que ele termine
    subprocess.run(cmd)

    # 3. Ler os resultados do XML gerado
    if not os.path.exists(results_xml):
        print(f"[red]Erro: Ficheiro de testes {results_xml} não foi gerado. Verifica o {log_file}[/red]")
        return False

    print("\n[bold yellow]📊 RESULTADOS DOS TESTES UNITÁRIOS (C#)[/bold yellow]")
    try:
        tree = ET.parse(results_xml)
        root = tree.getroot()
    except Exception as e:
        print(f"[red]Erro ao ler o ficheiro XML de testes: {e}[/red]")
        return False

    # O formato NUnit guarda o resumo na tag <test-run>
    total = root.attrib.get('total', '0')
    passed = root.attrib.get('passed', '0')
    failed = root.attrib.get('failed', '0')

    print(f"Total de Testes: {total} | [green]Passaram: {passed}[/green] | [red]Falharam: {failed}[/red]\n")

    # Mostra o detalhe de cada teste que falhou
    all_passed = (int(failed) == 0)

    for test_case in root.iter('test-case'):
        result = test_case.attrib.get('result')
        name = test_case.attrib.get('name')

        if result == "Passed":
            print(f"[green]✅ {name}[/green]")
        elif result == "Failed":
            print(f"[red]❌ {name}[/red]")
            # Apanha a mensagem de erro (o Assert que falhou)
            failure = test_case.find('failure')
            if failure is not None:
                message = failure.find('message')
                if message is not None:
                    print(f"   [gray]Motivo: {message.text.strip()}[/gray]")

    # Retorna True se tudo passou, False se algo falhou
    return all_passed

if __name__ == "__main__":
    run_unity_tests()