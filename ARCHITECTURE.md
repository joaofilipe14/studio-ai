# ARCHITECTURE.md — System Architecture

## Visão Geral
O sistema Studio-AI é dividido em três camadas independentes para garantir a separação de lógica de motor, definição de jogo e inteligência evolutiva.

---

## 1. Engine Layer (Unity)
Responsável pela simulação física, renderização e execução das regras.
- **Entrada**: `game_genome.json` (Parâmetros de geração e comportamento).
- **Processamento**:
    - **BuildScript**: Script de Editor que gera a cena, posiciona objetos e valida a navegabilidade via NavMesh.
    - **GameManager**: Controla o estado da simulação (Rondas, Resets e Timers).
- **Saída**: `metrics.json` (Exportação de performance do agente e estatísticas da ronda).

## 2. Game Definition Layer (Genome)
Define o jogo estritamente como dados estruturados.
- **Genome**: Um ficheiro JSON que contém todos os parâmetros (velocidade, número de obstáculos, tempo limite).
- **Seed**: Um valor numérico que garante que a geração procedimental é determinística e reproduzível.

## 3. Evolution Layer (Python/AI)
O "Cérebro" que orquestra o ciclo de vida do jogo.
- **Orchestrator**: Gere o fluxo `Planeamento -> Build -> Execução -> Avaliação`.
- **Director**: Analisa o `metrics.json` e aplica mutações ao `game_genome.json` para ajustar a dificuldade (ex: aumentar obstáculos se o sucesso for de 100%).