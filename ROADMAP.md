# ROADMAP.md — Autonomous Game Evolution (Studio-AI)

## Visão Geral
O objetivo final do **Studio-AI** é criar um "Desenvolvedor Virtual" capaz de gerar, balancear e distribuir conteúdo de jogo de forma contínua e autónoma. O sistema usa *Large Language Models* (LLMs) como Diretores de Jogo, ajustando parâmetros para manter os jogadores num estado de *flow* (desafio ideal).

---

## Fase 1 — Estabilidade e Loop de Feedback ✅ (Concluída)
*(Motor Parametrizado, Exportação de Métricas, Diretor de IA via Ollama, DB SQLite)*

## Fase 2 — Modos de Jogo e Complexidade Emergente 🚀 (Em Progresso)
- [x] **Diversidade de Modos:** Modos "PointToPoint" e "Collect".
- [x] **Geração Procedural Avançada:** *Drunkard's Walk* para Labirintos.
- [x] **Power-Ups e Armadilhas:** Modificadores de tempo e armadilhas.
- [ ] **Visão Limitada (Fog of War):** Adicionar mecânicas de exploração onde o mapa está oculto (essencial para o terror de ficar encurralado na "Fuga").
- [ ] **Densidade de Labirinto Real:** Alterar a geração de obstáculos para garantir corredores densos em vez de campos abertos.

## Fase 3 — Observabilidade e Dashboards (Data Science) 📊 ✅ (Concluída)
*(Dashboard Streamlit, Visualização de Tendências, Explorador de Genomas)*

## Fase 4 — O "Game Loop" Roguelite (Telemetria Humana) 👤 (Em Progresso)
*Transformar o protótipo de IA num Action Roguelite de Sobrevivência.*
- [x] **Telemetria de Jogador:** O jogo distingue Humanos de Bots.
- [x] **Diretor de IA de Empatia:** A IA reage à frustração humana facilitando o jogo.
- [ ] **Sistema de Moeda Dupla:** Implementar no Unity a separação entre "Moedas Apanhadas" (Ouro) e "Tempo Sobrante" (Cristais de Tempo) no ecrã de vitória.
- [ ] **Hub / Main Menu (A Loja):** Uma cena inicial no Unity onde o jogador gasta o Ouro e os Cristais para comprar Upgrades Globais e Personagens.
- [ ] **Sistema de Personagens (Classes):** Criar no Unity diferentes perfis de jogador (ex: Rápido/Frágil vs Lento/Resistente) que multiplicam as variáveis do `game_genome.json`.

## Fase 5 — Lançamento Autónomo (Cloud e Modding) ☁️
*O Santo Graal: O jogo "vive" num servidor e evolui para toda uma comunidade.*
- [ ] **Backend de Servidor (FastAPI):** Migrar a lógica do Orquestrador Python para a *cloud*.
- [ ] **A "Daily Run" (Desafio Diário):** Sincronizar o cliente Unity com um genoma único gerado todas as madrugadas pela IA, com Leaderboards para ver quem ganha mais Moeda/Tempo.