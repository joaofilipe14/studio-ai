# ROADMAP.md — Autonomous Game Evolution

## Fase 1 — Estabilidade e Loop de Feedback ✅ (Concluída)
- [x] **Implementação NavMesh**: Substituída a movimentação manual do `SimpleAgent` pelo componente `NavMeshAgent` para navegação robusta.
- [x] **Validador de Path / Bake**: O `BuildScript` assa (bakes) a malha de navegação automaticamente para garantir que o nível gerado tem caminhos válidos.
- [x] **Exportação de Métricas**: `GameManager` salva `metrics.json` com `win_rate`, `avg_time_to_goal` e `stuck_events`.

## Fase 2 — Engine Parametrizada (Genome Loading) ✅ (Concluída)
- [x] **Runtime/Build Loader**: O `BuildScript` e o `GameManager` leem o `game_genome.json` nativamente via `JsonUtility`.
- [x] **Geração Procedimental**: Criação de obstáculos, scaling e regras de arena dinâmicas baseadas estritamente nos valores ditados pelo genoma.

## Fase 3 — O Diretor de IA (Evolução) ✅ (Concluída)
- [x] **Análise de Performance**: Script Python (`orchestrator.py` via `run_game_simulation`) roda o jogo em headless e extrai as métricas.
- [x] **Mutação Automática**: A IA (Ollama) atua como "Director", avalia os resultados e reescreve automaticamente o `game_genome.json` para tentar atingir um alvo de dificuldade (ex: 60%-80% de taxa de sucesso).

## Fase 4 — Diversidade de Conteúdo (Foco Atual) 🚀
- [ ] **Validação Estrita de Path**: Implementar `NavMesh.CalculatePath` no `BuildScript` para rejeitar/regenerar instantaneamente *seeds* impossíveis (ex: objetivo bloqueado por paredes) antes de compilar o executável.
- [ ] **Modos de Jogo**: Adicionar suporte a templates como "Maze" (Labirinto denso), "Collect" (Múltiplas Moedas) e "Survival".
- [ ] **Hall of Fame**: Script Python para arquivar automaticamente os ficheiros `game_genome.json` que geraram os jogos com o melhor equilíbrio (perto do *sweet spot* de 70% win rate).

## Fase 5 — Complexidade Emergente
- [ ] **Inimigos Dinâmicos**: Introduzir agentes adversários (`ChaserAgents`) com velocidade e contagem controladas pelo genoma.
- [ ] **Power-ups e Condições**: Elementos no mapa que alteram a velocidade do agente ou o tempo limite.
- [ ] **Curvas de Progressão**: O `game_genome.json` definir um "Modo Campanha" de 10 níveis crescentes, em vez de apenas repetir a mesma ronda.