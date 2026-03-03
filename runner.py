import yaml
import time
import sys
import os
from rich import print

# Importamos o main limpo do orchestrator
from scripts.orchestrator import main as run_orchestrator

def main_runner():
    # 1. Carregar Configuração
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        print(f"[ERRO] Falha ao ler o config.yaml: {e}")
        sys.exit(1)

    # 2. Ler parâmetros de execução do YAML (agora só precisamos do número total de runs)
    run_section = config.get('run', {})
    # Vamos fazer 10 simulações seguidas por defeito
    total_runs = run_section.get('num_runs', 5)

    print("=" * 60)
    print(f" 🏃 RUNNER DE CAMPANHA INICIADO (FASE 4)")
    print(f" O Bot vai jogar e testar a Campanha com os modos originais!")
    print(f" Total de simulações: {total_runs}")
    print("=" * 60 + "\n")

    for i in range(1, total_runs + 1):
        print(f"\n>>> GERAÇÃO {i}/{total_runs} (Avaliação de Campanha) <<<")

        try:
            # O Orquestrador executa a Simulação e a Evolução
            # O Bot vai simplesmente jogar a campanha até morrer e a IA conserta o gargalo!
            run_orchestrator()
        except Exception as e:
            erro_msg = str(e)
            print(f"\n[bold red][ERRO NA GERAÇÃO] Falha na execução:[/bold red] {erro_msg}")

            # Proteção contra falhas do Ollama
            if "10061" in erro_msg or "Max retries exceeded" in erro_msg or "ConnectionRefused" in erro_msg:
                print("\n[bold red]🚨 ALERTA CRÍTICO: O servidor Ollama está desligado![/bold red]")
                print("[yellow]Por favor, liga o Ollama (abre a aplicação ou corre 'ollama serve' no terminal).[/yellow]")
                sys.exit(1)
            else:
                print("\n[bold red]🚨 Erro fatal desconhecido. A interromper o Runner por segurança.[/bold red]")
                sys.exit(1)

        # Pausa para o sistema respirar
        time.sleep(2)

    print("\n" + "=" * 60)
    print(f" 🎉 AVALIAÇÃO DE CAMPANHA CONCLUÍDA: {total_runs} GERAÇÕES PROCESSADAS")
    print("=" * 60)

if __name__ == "__main__":
    main_runner()