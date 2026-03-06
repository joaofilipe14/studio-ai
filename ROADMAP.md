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

## Fase 4 — O "Game Loop" Roguelite (Metajogo) 👤
- [x] **Polimento da Câmara:** Suavização com SmoothDamp concluída.
- [x] **Glossário de Itens:** Manual de sobrevivência básico implementado.
- [x] **Botão de Reiniciar:** Sistema de reset de save operacional.
- [ ] **Game Feel (Juice):** Implementar Screen Shake e Partículas de Voxels.
- [ ] **Feedback Sonoro:** Adicionar biblioteca de SFX (passos, moedas, dano).

## Fase 5 — Lançamento Server-Side e Mobile Cloud ☁️📱
- [ ] **Otimização Crítica:** Implementar Mesh Combiner no VoxelRenderer para performance mobile.
- [ ] **Controlos Táteis:** Criar o Joystick Virtual e suporte a gestos (swipes).
- [ ] **Backend Cloud:** Migrar o game_director.py para FastAPI.
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