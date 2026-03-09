# 🗺️ ROADMAP.md — Studio-AI: O Ecossistema Autónomo

## 🚀 Visão Geral
Transformar o Studio-AI de um protótipo funcional num estúdio de produção contínua, onde a IA gera o código, a arte, o som e a própria estratégia de marketing.

---

## Fase 4 — Game Feel, Som & Metajogo (Conclusão) 👤
*Foco: Impacto físico, feedback sonoro e retenção do jogador.*
- [x] **Polimento da Câmara:** Suavização com `SmoothDamp` implementada.
- [x] **Glossário de Itens:** Manual de sobrevivência básico operacional.
- [ ] **Juice Visual (Física):**
    - [ ] **Screen Shake:** Tremor de ecrã em impactos (danos/vitórias).
    - [ ] **Voxel Particles:** Explosão de cubos com `Rigidbody` ao coletar moedas ou morrer.
- [ ] **Sonoplastia Dinâmica:**
    - [ ] **SFX Encurtados:** Limitar sons de Moeda/Win/Lose a máx. 2 segundos para evitar estática.
    - [ ] **Mixagem:** Baixar Background Music para 25% e manter SFX a 100%.
- [ ] **Feedback de Save:** Indicador visual de progresso guardado.

## Fase 5 — Agente de Marketing & Persistência 🚀 (NOVA)
*Foco: Automação da comunicação e segurança de dados.*
- [ ] **Marketing Agent (`brain/marketing_agent.py`):**
    - [ ] Integração com Ollama para ler `evolution.db` e gerar posts contextuais.
    - [ ] Criação de legendas baseadas em vitórias reais ou novos recordes.
- [ ] **Marketing Hub (Dashboard):**
    - [ ] **Calendário Semanal:** Visualização de 7 dias de posts na Navbar Lateral.
    - [ ] **Persistência Segura:** Salvar planos em `memory/marketing_plan.json` (protegido de resets).
    - [ ] **Fluxo de Review:** Sistema de aprovação manual antes da exportação final.
- [ ] **Gerador de Trailers:** Script Unity para captura orbital (Hero Shot) de novos níveis.

## Fase 6 — Otimização Crítica & Cloud Mobile ☁️📱
*Foco: Performance para dispositivos móveis e infraestrutura web.*
- [ ] **Otimização de Render:** Implementar `Mesh Combiner` no `VoxelRenderer` para reduzir Draw Calls.
- [ ] **Backend Robusto (FastAPI):**
    - [ ] Migrar lógica do `game_director.py` e `marketing_agent.py` para uma API REST.
    - [ ] Desacoplar o Dashboard do Streamlit para uma arquitetura Client-Server.
- [ ] **Versão Mobile (Android/iOS):**
    - [ ] Joystick Virtual e controlos por gestos (Swipes).
    - [ ] UI Adaptativa (Anchors) para diferentes resoluções.

## Fase 7 — Ecossistema & Monetização 💰
*Foco: Comunidade, venda de assets e expansão de géneros.*
- [ ] **Discord Command Center:** Bot para reportar novos níveis e permitir votações da comunidade.
- [ ] **Asset Store Exporter:** Ferramenta para empacotar e vender texturas/sons gerados pela IA.
- [ ] **Evolução do Gameplay:** Transição de Rouglite simples para *Auto-Battler* ou *Narrative Dungeon Crawler*.
- [ ] **Migração Frontend:** Reescrita do Dashboard em **React** ou **Angular** para maior interatividade.