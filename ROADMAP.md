# ROADMAP.md — Autonomous Game Evolution (Studio-AI)

## Visão Geral
O objetivo final do **Studio-AI** é criar um "Desenvolvedor Virtual" capaz de gerar, balancear e distribuir conteúdo de jogo de forma contínua e autónoma. O sistema usa *Large Language Models* (LLMs) como Diretores de Jogo, ajustando parâmetros para manter os jogadores num estado de *flow* (desafio ideal).

---

## Fase 1 — Estabilidade e Loop de Feedback ✅ (Concluída)
- [x] **Motor Parametrizado:** O Unity lê o `game_genome.json` e gera o nível com base nesses dados.
- [x] **Exportação de Métricas:** O `GameManager` grava resultados (`metrics.json`) de forma *headless*.
- [x] **Diretor de IA (Evolução):** O script Python orquestra a simulação e o Ollama muta o genoma para atingir um *win rate* de 60%-80%.
- [x] **Registo de Evolução (SQLite):** Gravação de todo o histórico de mutações e métricas na `evolution.db`.

## Fase 2 — Modos de Jogo e Complexidade Emergente 🚀 (Em Progresso)
- [x] **Diversidade de Modos:** Implementação lógica de modos distintos como "PointToPoint" e "Collect" com comportamentos de Agente adaptáveis.
- [x] **Anti-Sobreposição de Spawn:** Algoritmo de grelha que garante que o jogador, inimigos e itens nascem em posições únicas e justas.
- [x] **Controlo Híbrido:** Capacidade de alternar entre IA (`SimpleAgent`) e controlo manual do Jogador (WASD) lendo o `userControl` do genoma.
- [ ] **Geração Procedural Avançada:** Atualizar o `GridWorld` para gerar "Labirintos" (com corredores definidos) em vez de apenas blocos aleatórios.
- [ ] **Power-Ups e Armadilhas:** Introduzir mecânicas que afetem o tempo (ex: relógios) ou a velocidade, permitindo à IA mais formas de equilibrar o jogo.
- [ ] **Visão Limitada (Fog of War):** Adicionar mecânicas de exploração onde o mapa está oculto.

## Fase 3 — Observabilidade e Dashboards (Data Science) 📊 (Próxima)
- [ ] **Dashboard Streamlit (`dashboard.py`):** Criar uma interface web interativa para ler a base de dados `evolution.db`.
- [ ] **Visualização de Tendências:** Gráficos de linha a mostrar a evolução do `win_rate` ao longo das gerações vs `enemy_speed` e `agent_speed`.
- [ ] **Explorador de Genomas:** Tabela interativa para ler os `ai_reports` e fazer download do JSON exato de qualquer geração passada.
- [ ] **Comparação de Modos:** Gráficos de barras a comparar a taxa de sucesso e o tempo médio entre o modo "Collect" e "PointToPoint".

## Fase 4 — Telemetria Humana e O "Game Loop" 👤
Nesta fase, o jogo passa a aprender com o comportamento de humanos, em vez de bots.
- [ ] **Métricas Locais de Jogador:** O executável do jogo regista mapas de calor (onde o jogador morre mais) e tempo de decisão.
- [ ] **Evolução Focada no Humano:** O orquestrador Python altera o seu *prompt* para ler os dados do jogador humano e gerar um desafio à medida.
- [ ] **Meta-Progressão (Modo Campanha):** Em vez de jogar o mesmo nível iterativamente, o jogador avança de "Dia 1" para "Dia 2", recebendo um genoma inteiramente novo se vencer.
- [ ] **Economia e Assets:** Uso de moedas coletadas para desbloquear cosméticos visuais.

## Fase 5 — Lançamento Autónomo (Cloud e Modding) ☁️
O Santo Graal: O jogo "vive" num servidor e evolui para toda uma comunidade sem intervenção humana.
- [ ] **Backend de Servidor (FastAPI):** Migrar a lógica do Orquestrador Python para uma API na *cloud*.
- [ ] **Sincronização Diária:** O cliente (Unity) pede ao servidor o genoma do "Desafio Diário" assim que o jogador abre o jogo.
- [ ] **Balanceamento de Comunidade:** O Diretor IA recolhe métricas de milhares de jogadores e lança um patch no dia seguinte para corrigir níveis fáceis/difíceis.
- [ ] **Injeção de Assets Gerados por IA:** Integração com *Stable Diffusion* para mudar texturas do chão e *MusicGen* para criar novos *loops* musicais com base no "clima" que a IA quiser para o nível.