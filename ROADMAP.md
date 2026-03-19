# 🗺️ ROADMAP.md — Studio-AI: O Ecossistema Autónomo

## 🚀 Visão Geral
Transformar o Studio-AI de um protótipo funcional num estúdio de produção contínua, onde a IA gera o código, a arte, o som e a própria estratégia de marketing.

---

## Fase 4 — Game Feel, Som & Metajogo (Concluída) 🟢
*Foco: Impacto físico, feedback sonoro e retenção do jogador.*
- [x] **Polimento da Câmara:** Suavização com `SmoothDamp` implementada.
- [x] **Glossário de Itens:** Manual de sobrevivência básico operacional.
- [x] **Juice Visual (Física):** Screen Shake e Voxel Particles físicos.
- [x] **Sonoplastia Dinâmica:** Canais Separados (Música e Efeitos).
- [x] **Sistema de Save Humano:** `player_save.json` funcional.

## Fase 5 — Arquitetura Server-Client & Analytics (Concluída) 🟢
*Foco: Escalabilidade e painel de controlo profissional.*
- [x] **Backend Robusto (FastAPI):** APIs REST para comunicação jogo-servidor.
- [x] **Migração Frontend (React):** Dashboard Cyberpunk.
- [x] **Métricas em Tempo Real:** SQLite (`evolution.db`) integrado.
- [x] **Hall of Fame:** Algoritmo para isolar "Masterpieces".

## Fase 6 — Automação de Marketing & Dashboard Central (Quase Concluída) 🟡
*Foco: Automação da comunicação e visão unificada do Estúdio.*
- [x] **Marketing Agent:** Integração LLM para posts e legendas temáticas.
- [x] **Dashboard Resumo (Home):** UI React agregando estatísticas globais e estado da IA.
- [x] **Gerador de Trailers (Unity):** Drone Policial/Render Farm Autónoma para vídeos promocionais.
- [ ] **Integração de Redes Sociais:** Exportar pipeline para publicação via API (Twitter/Discord).

---

## Fase 7 — O Ciclo Roguelite & As Lojas Dinâmicas (Concluída) 🟢
*Foco: Transição de "Proof of Concept" para Jogo Indie Completo com Meta-Progresso.*
- [x] **O Hub Dinâmico (O Cofre):**
    - [x] Refatorar UXML/USS para usar Grelhas Flexíveis e design Premium Cyberpunk.
    - [x] Ligar o C# ao `roster.json` para gerar Cartas de Classes e Upgrades proceduralmente.
    - [x] Lógica de compra: Validar e descontar os "Cristais de Tempo" no `player_save.json`.
- [x] **O Mercado Negro (Safe Room):**
    - [x] Intercetar os Níveis 3, 6 e 9 com um ecrã de Loja In-Game.
    - [x] Sistema de Drop Rate dinâmico com Raridades (Comum, Incomum, Raro) gerido pelo `safe_room_items.json`.
    - [x] Descontar "Moedas de Ouro" ganhas na Run atual.
- [x] **Orquestração Python Automática:**
    - [x] O `tool_runner.py` injeta JSONs, UXMLs, USSs e CS dinamicamente na *Build* final sem *hardcoding*.
- [ ] **Implementação Funcional dos Power-Ups:** *(NOVO)*
    - [ ] Ligar variáveis temporárias (Safe Room) e permanentes (Cofre) ao `GameManager.cs`.
    - [ ] Garantir que o Boost de Tempo adiciona segundos reais ao HUD e que a Vida Extra atualiza o limite de danos.
- [ ] **Implementação Visual dos Power-Ups (Juice):** *(NOVO)*
    - [ ] **UI:** Feedback visual na compra (ex: o relógio pisca a verde quando se compra tempo, partículas de dinheiro a voar).
    - [ ] **In-Game:** Feedback visual no Agente (ex: rasto de luz/partículas quando tem o *Speed Boost*, cone da lanterna aumenta visivelmente e muda de cor com o *Vision Boost*).
  
## Fase 8 — Agente de Game Design (Expansão de Conteúdo Infinita) 🤖 (PRÓXIMO PASSO)
*Foco: A IA inventa novas expansões de jogo sozinha (Personagens, Upgrades e Arte).*
- [ ] **O Arquiteto de Conteúdo (Python + LLM):**
    - [ ] A IA gera ideias para novos Heróis e Power-Ups com mecânicas únicas.
    - [ ] Auto-atualiza o `roster.json` e o `safe_room_items.json` com os novos dados e custos equilibrados.
- [ ] **Integração Visual Automática:**
    - [ ] O Agente escreve os novos prompts de imagem no `assets_recipes.json`.
    - [ ] O Agente injeta automaticamente as novas classes CSS no `SafeRoomStyle.uss` e `VaultStyle.uss` para ligar as imagens geradas à UI.
- [ ] **Mecânicas de Tensão In-Game (Risk vs Reward):**
    - [ ] **Moedas Amaldiçoadas:** Apanhar moedas in-game ativa um trigger que aumenta a velocidade dos inimigos nesse nível.
    - [ ] **O Modo Pânico:** Quando o relógio desce dos 15s, a iluminação global fica vermelha e a música acelera.

## Fase 9 — Cosmética, Sonoplastia & Direção de Arte IA 🎨🎵
*Foco: Fazer o jogo parecer um produto premium.*
- [ ] **Post-Processing (Maquilhagem do Unity):**
    - [ ] Integração do Universal Render Pipeline (URP).
    - [ ] Adicionar Global Volume: *Bloom* (brilho neon extremo) e *Color Grading* dinâmico por bioma.
- [ ] **Agente de Arte 2.0 (Texturas IA):**
    - [ ] Ligar o backend a modelos SD/DALL-E para gerar *Seamless Textures* (chão enferrujado, poças de ácido).
- [ ] **Agente de Áudio IA:**
    - [ ] Implementar geração de música procedural (MusicGen/AudioCraft) que reage à proximidade da morte.

## Fase 10 — Otimização, Portabilidade Mobile & Monetização ☁️📱
*Foco: Levar o jogo para Android/iOS e rentabilizar o ecossistema autónomo.*
- [ ] **Arquitetura Mobile:** Input System para Touch e Joysticks Virtuais.
- [ ] **Otimização Extrema:** Implementar `Mesh Combiner` e `GPU Instancing` nos cubos voxel.
- [ ] **Asset Store Exporter Autonómo:** Um script Python que empacota prefabs/texturas num `.unitypackage` para vender na Unity Asset Store.