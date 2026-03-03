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

## Fase 3 — Observabilidade e Dashboards (Data Science) 📊 ✅ (Fevereiro 2026)
- [x] Dashboard Streamlit com separação de Tabs (Métricas vs Arte).
- [x] Visualização de Tendências por Modo de Jogo e por Nível.
- [x] Diff Automático de Genomas e Logs do Diretor IA.
- [x] Estúdio de Arte IA: Geração de Asset Packs (8 texturas/sprites) via SDXL + Rembg.

---

## Fase 4 — O "Game Loop" Roguelite (Metajogo) 👤 (Em curso)
*Foco em Polimento, UX e Retenção de Jogadores.*

- [x] **Refactorização Genética:** Divisão do genome em listas de níveis, roster e saves.
- [x] **Sistema de Personagens:** Escolha de classes via `roster.json` e compra de vidas.
- [ ] **Polimento da Câmara:** Suavizar a transição e rotação da câmara para evitar mudanças bruscas que causam tonturas.
- [ ] **Glossário de Itens:** Adicionar um ecrã ou menu de ajuda que explique o que faz cada item (Moedas, Power-ups, Armadilhas).
- [ ] **Sistema de Checkpoint/Save-Time:** Implementar um indicador de quando o jogo foi guardado ou permitir guardar progresso a meio da run.
- [ ] **Botão de Reiniciar:** Adicionar um botão "Recomeçar Campanha" no menu ou após o Game Over para limpar o progresso atual.
- [ ] **UI Adaptativa:** Melhorar os menus para resoluções variadas e preparar para interações táteis.

## Fase 5 — Lançamento Server-Side e Mobile Cloud ☁️📱
*Preparar o sistema para viver na Web e em dispositivos móveis.*

- [ ] **Backend Cloud (FastAPI):** Migrar a evolução da IA para um servidor remoto (essencial para Mobile).
- [ ] **Versão Mobile (Android/iOS):**
    - [ ] Implementar Joystick Virtual para movimento tátil.
    - [ ] Otimização de Voxels para performance em telemóveis.
    - [ ] Interface de utilizador escalável para ecrãs pequenos.
- [ ] **Telemetria Global:** Base de dados na cloud para comparar performance entre jogadores PC e Mobile.
- [ ] **Leaderboards Globais:** Tabela de pontuações sincronizada via API.

## Fase 6 — Deploy Final & Polimento 🚀
- [ ] **Lançamento Multiplataforma:** PC (Itch.io) e Mobile (APK/App Store).
- [ ] **Auto-Patching:** Download de assets (sprites/texturas) dinamicamente via API.