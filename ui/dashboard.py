import streamlit as st
import plotly.express as px
import json
import os
# Importações do sistema
from db.evolution_logger import get_evolution_history
from brain.art_director import (
    generate_character_prompt,
    generate_art_asset,
    TEMPLATE_SPRITES,
    TEMPLATE_TEXTURES
)

# Configurações de layout
st.set_page_config(page_title="Studio-AI: Director Control", layout="wide")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "logs", "evolution.db")

st.title("📊 Studio-AI: Director Control")

# Carregar dados uma única vez
df = get_evolution_history(DB_PATH)

if df.empty:
    st.warning("⚠️ Base de dados vazia. Executa uma simulação primeiro!")
else:
    # --- ORGANIZAÇÃO POR TABS ---
    tab_metrics, tab_art = st.tabs(["📈 Análise de Performance", "🎨 Estúdio de Assets"])

    # ==========================================
    # TAB 1: ANÁLISE DE MÉTRICAS E JSON
    # ==========================================
    with tab_metrics:
        st.header("Análise de Evolução e Genomas")

        # Filtros Rápidos na Lateral (Apenas para Métricas)
        st.sidebar.header("🔍 Filtros de Análise")
        modos = df['game_mode'].unique().tolist()
        modo_f = st.sidebar.multiselect("Filtrar Modos:", modos, default=modos)

        df_filtered = df[df['game_mode'].isin(modo_f)]

        if df_filtered.empty:
            st.error("Nenhum dado para os filtros selecionados.")
        else:
            # Métricas em destaque
            latest = df_filtered.iloc[0]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Win Rate Atual", f"{latest['win_rate']:.2f}")
            m2.metric("Velocidade Inimigo", f"{latest['enemy_speed']} m/s")
            m3.metric("Obstáculos", latest['obstacles_count'])
            m4.metric("Modo Atual", latest['game_mode'])

            st.divider()

            # Gráfico de Tendência
            fig = px.line(
                df_filtered.sort_values('id'),
                x='id',
                y='win_rate',
                color='game_mode',
                markers=True,
                title="Evolução da Taxa de Vitória",
                labels={'id': 'ID da Geração', 'win_rate': 'Win Rate'}
            )
            fig.update_layout(yaxis_range=[0, 1.1])
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Inspeção de JSON e Relatórios
            st.subheader("🔍 Detalhes Técnicos da Geração")
            all_ids = df_filtered['id'].tolist()
            selected_id = st.select_slider("Arrasta para inspecionar um ID específico:", options=all_ids)

            detail = df[df['id'] == selected_id].iloc[0]
            col_report, col_json = st.columns([1, 1])

            with col_report:
                st.info(f"**Relatório do Diretor (ID #{selected_id}):**\n\n{detail['ai_report']}")
            with col_json:
                st.write("**Genoma Aplicado:**")
                st.json(json.loads(detail['genome_json']))
            st.divider()
            st.subheader("🔍 Inspeção Técnica e Comparação")

            all_ids = df_filtered['id'].tolist()
            selected_id = st.select_slider("Selecione um ID para inspecionar e comparar com o anterior:", options=all_ids)

            # 1. Detalhes da geração selecionada
            detail = df[df['id'] == selected_id].iloc[0]
            genome_atual = json.loads(detail['genome_json'])
            modo_alvo = genome_atual.get("mode", detail['game_mode']) # O modo real dentro do JSON

            # 2. Procurar o genoma anterior do MESMO MODO lendo diretamente os JSONs
            df_anteriores = df[df['id'] < selected_id].sort_values('id', ascending=False)

            prev_detail = None
            genome_anterior = None

            for _, row in df_anteriores.iterrows():
                try:
                    g = json.loads(row['genome_json'])
                    if g.get("mode") == modo_alvo: # Garante separação total de modos!
                        prev_detail = row
                        genome_anterior = g
                        break # Encontrou o imediatamente anterior do mesmo modo
                except Exception:
                    continue

            # 3. Mostrar os Dados e o Diff
            if prev_detail is not None:
                col_prev, col_diff, col_next = st.columns([1, 0.6, 1])

                with col_prev:
                    st.write(f"⬅️ **Anterior (#{prev_detail['id']} - {modo_alvo})**")
                    st.json(genome_anterior)

                with col_diff:
                    st.write("🔄 **Mudanças**")
                    # Compara valores numéricos entre genomas
                    for section in ["rules", "agent", "obstacles"]:
                        if section in genome_atual and section in genome_anterior:
                            for k, v in genome_atual[section].items():
                                if isinstance(v, (int, float)) and k in genome_anterior[section]:
                                    old_v = genome_anterior[section][k]
                                    if v != old_v:
                                        diff = v - old_v
                                        color = "green" if diff > 0 else "red"
                                        st.markdown(f"**{k}**:  \n{old_v} ➡️ {v}  \n(:{color}[{diff:+.2f}])")

                with col_next:
                    st.write(f"➡️ **Selecionado (#{selected_id} - {modo_alvo})**")
                    st.json(genome_atual)
            else:
                st.info(f"ℹ️ Esta é a primeira geração registada para o modo '{modo_alvo}'. Sem comparação disponível.")
                st.json(genome_atual)

            st.info(f"**Relatório da IA para ID #{selected_id}:** {detail['ai_report']}")

    # ==========================================
    # TAB 2: GERAÇÃO DE ASSETS (ART STUDIO)
    # ==========================================
    with tab_art:
        st.header("🎨 Geração de Assets por IA")
        st.write("Usa as APIs locais do Stable Diffusion e Ollama para criar novos elementos visuais.")

        col_hero, col_world = st.columns(2)

        with col_hero:
            st.subheader("👤 Herói & Sprites")
            st.write("Gera um novo Ninja ou Marine baseado nos últimos atributos.")

            if st.button("✨ Criar Novo Herói"):
                with st.spinner("IA a imaginar e desenhar..."):
                    # Usamos o genoma mais recente para ditar o estilo
                    latest_genome = json.loads(df.iloc[0]['genome_json'])
                    prompt = generate_character_prompt(latest_genome)
                    sprite_path = os.path.join(TEMPLATE_SPRITES, "PlayerSprite.png")

                    # Chamada unificada da função de arte
                    generate_art_asset(prompt, sprite_path, is_sprite=True)
                    st.success("✅ Sprite guardado em Templates!")
                    st.image(sprite_path, caption="Preview do Herói", width=300)

        with col_world:
            st.subheader("🌍 Ambiente & Texturas")
            tema_mundo = st.selectbox("Escolha o bioma do labirinto:",
                                      ["Cyberpunk Neon", "Medieval Dungeon", "Alien Hive", "Frozen Cave"])

            if st.button("🌍 Gerar Novas Texturas"):
                with st.spinner(f"A criar materiais para {tema_mundo}..."):
                    # Prompts baseados no bioma selecionado
                    floor_p = f"top-down view, {tema_mundo.lower()} floor tiles, seamless pattern, pixel art, flat colors"
                    obs_p = f"top-down view, {tema_mundo.lower()} wall pillar, metal crate, pixel art, flat colors"

                    # Gerar assets de ambiente (is_sprite=False para não remover fundo)
                    generate_art_asset(floor_p, os.path.join(TEMPLATE_TEXTURES, "FloorTexture.png"), is_sprite=False)
                    generate_art_asset(obs_p, os.path.join(TEMPLATE_TEXTURES, "ObstacleTexture.png"), is_sprite=False)

                    st.success(f"✅ Materiais {tema_mundo} guardados!")
                    st.image(os.path.join(TEMPLATE_TEXTURES, "FloorTexture.png"), caption="Novo Chão", width=200)