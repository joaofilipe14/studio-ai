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
- [x] **Gerador de Trailers (Unity):** Drone Policial/Render Farm Autónoma para vídeos promocionais (Hero Shots).
- [ ] **Integração de Redes Sociais:** Exportar o pipeline de vídeo+texto do Agente para publicação via API (Twitter/Discord).

---

## Fase 7 — Evolução do Gameplay & Economia de Tempo ⏳ (PRÓXIMO PASSO)
*Foco: Transição de "Proof of Concept" para Jogo Indie Completo com Meta-Progresso.*
- [ ] **A Mecânica Híbrida (Risk vs Reward):**
    - [ ] Fundir `PointToPoint` e `Collect`. Todo o nível tem uma Meta (Portal) e Moedas de Alto Risco.
    - [ ] **Economia de Tempo:** Conversão automática dos segundos não utilizados na Meta em "Cristais de Tempo" (Moeda Premium).
- [ ] **Expansão para 20 Níveis (Os Setores):**
    - [ ] Níveis 1-10: Submundo Néon (Acesso livre).
    - [ ] Níveis 11-20: Zona Tóxica / Industrial.
- [ ] **Gatekeeping & O Cofre:**
    - [ ] Interface para gastar "Cristais de Tempo" a hackear a Firewall para o Setor 2.
- [ ] **Novos Elementos de Game Design (IA Level Director):**
    - [ ] **Inimigos Especializados:** *Patrulheiros* (rotas fixas) e *Snipers* (feixes de laser temporizados).
    - [ ] **Puzzles de Mapa:** Botões no chão necessários para abrir Portões Magnéticos de acesso à Meta.

## Fase 8 — Cosmética, Sonoplastia & Direção de Arte IA 🎨🎵
*Foco: Fazer o jogo parecer um produto premium através de conteúdos gerados por IA em tempo real.*
- [ ] **Post-Processing (Maquilhagem do Unity):**
    - [ ] Integração do Universal Render Pipeline (URP).
    - [ ] Adicionar Global Volume: *Bloom* (brilho neon extremo), *Vignette*, e *Color Grading* dinâmico por bioma.
- [ ] **Agente de Arte 2.0 (Texturas IA):**
    - [ ] Ligar o backend (Python) a modelos como Stable Diffusion/DALL-E para gerar *Seamless Textures* (chão enferrujado, poças de ácido) e exportar direto para a pasta `Resources` do Unity.
- [ ] **Agente de Áudio IA:**
    - [ ] Implementar geração de música procedural de tensão (modelos como MusicGen/AudioCraft). O som altera dependendo de quão perto a IA acha que o jogador está de morrer.
- [ ] **Ambiente Vivo e Juice 2.0:**
    - [ ] Letreiros de néon nas paredes com *glitches* (erros visuais intermitentes).
    - [ ] Animações *Idle* de respiração/flutuação para o Player e Inimigos.

## Fase 9 — Otimização, Portabilidade Mobile & Monetização ☁️📱
*Foco: Levar o jogo para Android/iOS e rentabilizar o ecossistema autónomo.*
- [ ] **Arquitetura Mobile:**
    - [ ] Implementação do novo *Input System* do Unity para Touch.
    - [ ] Joysticks Virtuais no ecrã e UI adaptativa (Anchors perfeitamente definidos).
- [ ] **Otimização Extrema de Performance:**
    - [ ] Implementar `Mesh Combiner` e `GPU Instancing` nos cubos voxel para reduzir centenas de Draw Calls para apenas uma.
    - [ ] Occlusion Culling para níveis muito grandes.
- [ ] **Discord Command Center:**
    - [ ] Bot interativo onde a comunidade pode votar em "sementes geradas pela IA" para ver quem consegue o melhor tempo num nível desenhado pelo computador.
- [ ] **Asset Store Exporter Autonómo:**
    - [ ] Um script Python que identifica os melhores prefabs/texturas gerados pela IA, empacota num `.unitypackage` e escreve as descrições para vender na Unity Asset Store.