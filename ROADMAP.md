# ROADMAP.md — Autonomous Game Evolution (Studio-AI)

## Visão Geral
O objetivo final do **Studio-AI** é criar um "Desenvolvedor Virtual" capaz de gerar, balancear e distribuir conteúdo de jogo de forma contínua e autónoma. O sistema usa *Large Language Models* (LLMs) como Diretores de Jogo, ajustando parâmetros para manter os jogadores num estado de *flow* (desafio ideal).

---

## Fase 1 — Estabilidade e Loop de Feedback ✅ (Fevereiro 2026)
*(Motor Parametrizado, Exportação de Métricas, Diretor de IA via Ollama, DB SQLite)*

## Fase 2 — Modos de Jogo e Complexidade Emergente ✅ (Fevereiro 2026)
- [x] **Diversidade de Modos:** Modos "PointToPoint" e "Collect".
- [x] **Geração Procedural Avançada:** *Drunkard's Walk* para Labirintos.
- [x] **Power-Ups e Armadilhas:** Modificadores de tempo e armadilhas.
- [x] **Visão Limitada (Fog of War):** Adicionada a mecânica de `visionRadius` com luz pontual.
- [x] **Densidade de Labirinto Real:** Transição de percentagens caóticas para limites absolutos (`obstacles.count`, `enemyCount`).

## Fase 3 — Observabilidade e Dashboards (Data Science) 📊 ✅ (Fevereiro 2026)
- [x] Dashboard Streamlit com separação de Tabs (Métricas vs Arte).
- [x] Visualização de Tendências por Modo de Jogo.
- [x] Diff Automático de Genomas e Logs do Diretor IA.
- [x] Integração de API de Arte (Geração de Sprites e Texturas via SDXL + Rembg).

---

## Fase 4 — O "Game Loop" Roguelite (Metajogo) 👤 (Início de Março 2026)
*Transformar o protótipo de IA num Action Roguelite de Sobrevivência com progressão.*
- [ ] **Refactorização Genética:** Dividir o `game_genome.json` em `level_genome.json`, `roster.json` e `player_save.json`.
- [ ] **Hub / Main Menu:** Uma cena inicial no Unity (Menu Principal).
- [ ] **Sistema de Personagens (Classes):** Implementar a escolha de classes (Ninja, Golem, Explorador) lidas a partir do `roster.json`.
- [ ] **A Loja (Upgrades):** Usar o `total_collected` guardado no `player_save.json` para comprar vantagens permanentes (mais tempo inicial, resistência a armadilhas).
- [ ] **Progressão de Dificuldade:** A IA começa a ditar temas visuais (ex: "Frozen Cave") com base no nível da campanha.

## Fase 5 — Lançamento Server-Side e API ☁️ (Meados de Março 2026)
*Preparar o sistema para viver fora do teu computador e comunicar com o mundo.*
- [ ] **Backend Cloud (FastAPI):** Extrair o `game_director.py` para uma API REST. O jogo pede níveis à cloud em vez de correr Python localmente.
- [ ] **Telemetria Global:** Base de dados na cloud (ex: Supabase/Firebase) para recolher *Win Rates* de dezenas de jogadores em simultâneo.
- [ ] **A "Daily Run" (Desafio Diário):** Sincronizar todos os clientes com o mesmo `level_genome.json` gerado na madrugada.
- [ ] **Leaderboards:** Tabela de pontuações global (Quem acabou mais rápido? Quem apanhou mais moedas?).

## Fase 6 — Deploy Final & Polimento 🚀 (Final de Março / Abril 2026)
*O Santo Graal: O jogo "vive" num servidor e evolui para toda uma comunidade.*
- [ ] **Exportação Final (Build):** Compilar executáveis otimizados para Windows, Mac e Linux (ou WebGL).
- [ ] **Auto-Patching:** O jogo descarrega os novos *Sprites* e *Texturas* da cloud dinamicamente sempre que a IA decide mudar o tema diário.
- [ ] **Lançamento (itch.io / Steam):** Publicar a página do jogo com os assets gerados pela própria IA.
- [ ] **Modding Support:** Permitir à comunidade criar os seus próprios `roster.json`.