import sys
import os
# 🚨 INJEÇÃO CRÍTICA: Garante que o Python encontra as pastas 'db' e 'brain' sempre!
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests  # 🚨 NOVO IMPORT PARA O HEALTH CHECK

# Importações do sistema
from db.evolution_logger import get_evolution_history
from brain.art_director import (
    generate_full_theme,
    TEMPLATE_SPRITES,
    TEMPLATE_TEXTURES, generate_single_asset, ASSET_RECIPES
)

# Configurações de layout
st.set_page_config(page_title="Studio-AI: Director Control", layout="wide")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "logs", "evolution.db")

st.title("📊 Studio-AI: Director Control")

# ==========================================
# 🩺 HEALTH CHECK VISUAL NA SIDEBAR
# ==========================================
st.sidebar.header("⚙️ Motores de IA")

def check_service(url):
    try:
        # Tenta ligar-se aos servidores (desiste ao fim de meio segundo para não bloquear o site)
        requests.get(url, timeout=0.5)
        return True
    except:
        return False

ollama_online = check_service("http://localhost:11434/")
sd_online = check_service("http://127.0.0.1:7860/")

st.sidebar.markdown(f"**🧠 Diretor Níveis (Ollama):** {'🟢 Online' if ollama_online else '🔴 Offline'}")
st.sidebar.markdown(f"**🎨 Diretor Arte (A1111):** {'🟢 Online' if sd_online else '🔴 Offline'}")

if not ollama_online or not sd_online:
    st.sidebar.warning("⚠️ Alerta: Tens motores desligados. Liga-os antes de correres simulações ou gerardes arte!")

st.sidebar.divider()
# ==========================================


# Carregar dados da Base de Dados
df = get_evolution_history(DB_PATH)

if df.empty:
    st.warning("⚠️ Base de dados vazia. Executa uma simulação primeiro!")
else:
    # 🛡️ Blindagem de segurança para garantir que lê DBs antigas e novas
    if 'is_human' not in df.columns:
        df['is_human'] = 0
    if 'level_id' not in df.columns:
        df['level_id'] = 1

    # --- ORGANIZAÇÃO POR TABS ---
    tab_metrics, tab_art = st.tabs(["📈 Análise de Performance", "🎨 Estúdio de Assets"])

    # ==========================================
    # TAB 1: ANÁLISE DE MÉTRICAS E JSON
    # ==========================================
    with tab_metrics:
        st.header("Análise de Evolução e Genomas")

        # Filtros Rápidos na Lateral
        st.sidebar.header("🔍 Filtros de Análise")

        modos = df['game_mode'].unique().tolist()
        modo_f = st.sidebar.multiselect("Filtrar Modos:", modos, default=modos)

        niveis = sorted(df['level_id'].unique().tolist())
        nivel_f = st.sidebar.multiselect("Filtrar Níveis:", niveis, default=niveis)

        st.sidebar.subheader("Tipo de Jogador")
        mostrar_humano = st.sidebar.checkbox("Incluir jogadas do Humano", value=True)
        mostrar_bot = st.sidebar.checkbox("Incluir jogadas do Bot (QA)", value=True)

        # 🎯 APLICAÇÃO DOS FILTROS (Versão 100% Segura para Pandas)
        mask = df['game_mode'].isin(modo_f) & df['level_id'].isin(nivel_f)

        player_mask = pd.Series(False, index=df.index)
        if mostrar_humano:
            player_mask = player_mask | (df['is_human'] == 1)
        if mostrar_bot:
            player_mask = player_mask | (df['is_human'] == 0)

        df_filtered = df[mask & player_mask]

        if df_filtered.empty:
            st.error("Nenhum dado para os filtros selecionados.")
        else:
            # Métricas em destaque
            latest = df_filtered.iloc[0]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Win Rate Atual", f"{latest['win_rate']:.2f}")
            m2.metric("Nível Inspecionado", f"Nível {latest['level_id']}")
            m3.metric("Obstáculos", latest['obstacles_count'])
            m4.metric("Modo Atual", latest['game_mode'])

            st.divider()

            # 📈 Gráfico de Tendência
            df_filtered = df_filtered.copy()
            df_filtered['Legenda'] = df_filtered.apply(
                lambda row: f"Lvl {row['level_id']} - {row['game_mode']} ({'Humano' if row['is_human'] else 'Bot'})", axis=1
            )

            fig = px.line(
                df_filtered.sort_values('id'),
                x='id',
                y='win_rate',
                color='Legenda',
                markers=True,
                title="Evolução da Taxa de Vitória (Curva de Aprendizagem)",
                labels={'id': 'ID da Geração', 'win_rate': 'Win Rate'}
            )
            fig.update_layout(yaxis_range=[0, 1.1])
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Inspeção de JSON e Relatórios
            st.subheader("🔍 Inspeção Técnica e Comparação")
            all_ids = df_filtered['id'].tolist()
            selected_id = st.select_slider("Selecione um ID para inspecionar e comparar com o anterior:", options=all_ids)

            # 1. Detalhes da geração selecionada
            detail = df[df['id'] == selected_id].iloc[0]
            genome_atual = json.loads(detail['genome_json'])
            modo_alvo = genome_atual.get("mode", detail['game_mode'])
            nivel_alvo = genome_atual.get("level_id", detail['level_id'])

            # 2. Procurar o genoma anterior do MESMO MODO e MESMO NÍVEL
            df_anteriores = df[df['id'] < selected_id].sort_values('id', ascending=False)
            prev_detail = None
            genome_anterior = None

            for _, row in df_anteriores.iterrows():
                try:
                    g = json.loads(row['genome_json'])
                    if g.get("mode") == modo_alvo and g.get("level_id", 1) == nivel_alvo:
                        prev_detail = row
                        genome_anterior = g
                        break
                except Exception:
                    continue

            # 3. Mostrar os Dados e o Diff
            if prev_detail is not None:
                col_prev, col_diff, col_next = st.columns([1, 0.6, 1])

                with col_prev:
                    st.write(f"⬅️ **Anterior (ID {prev_detail['id']} - Nível {nivel_alvo})**")
                    st.json(genome_anterior)

                with col_diff:
                    st.write("🔄 **Mutações**")
                    for section in ["rules", "agent", "obstacles", "arena"]:
                        if section in genome_atual and section in genome_anterior:
                            for k, v in genome_atual[section].items():
                                if isinstance(v, (int, float)) and k in genome_anterior[section]:
                                    old_v = genome_anterior[section][k]
                                    if v != old_v:
                                        diff = v - old_v
                                        color = "green" if diff > 0 else "red"
                                        st.markdown(f"**{k}**:  \n{old_v} ➡️ {v}  \n(:{color}[{diff:+.2f}])")

                with col_next:
                    st.write(f"➡️ **Selecionado (ID {selected_id} - Nível {nivel_alvo})**")
                    st.json(genome_atual)
            else:
                st.info(f"ℹ️ Esta é a primeira geração registada para o Nível {nivel_alvo} no modo '{modo_alvo}'.")
                st.json(genome_atual)

            st.info(f"**Relatório da IA (Diretor de Nível ID #{selected_id}):** {detail['ai_report']}")

    # ==========================================
    # TAB 2: GERAÇÃO DE ASSETS (ART STUDIO)
    # ==========================================
    with tab_art:
        st.header("🎨 Geração de Pacote Visual por IA")
        st.write("Usa o Stable Diffusion para criar elementos top-down perfeitos para a grelha do Unity.")

        tema_mundo = st.selectbox("Escolha o tema desejado para a próxima build:",
                                  ["Cyberpunk Neon", "Medieval Dungeon", "Alien Hive", "Frozen Cave", "Post-Apocalyptic Wasteland", "Retro 8-bit Arcade"])

        # 🚨 NOVO: Botões Lado-a-Lado para Geração Total vs Geração Individual
        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            st.write("**Gerar o Mundo Inteiro (Demora 2-3 min)**")
            if st.button(f"🚀 Gerar Pacote Completo", use_container_width=True):
                with st.spinner(f"A Direção de Arte está a criar o pacote '{tema_mundo}'..."):
                    try:
                        generate_full_theme({"theme": tema_mundo})
                        st.success(f"✅ Pacote completo gerado com sucesso!")
                    except Exception as e:
                        st.error(f"⚠️ Operação Abortada: {str(e)}")

        with col_btn2:
            st.write("**Corrigir Apenas 1 Elemento (Rápido)**")
            asset_to_fix = st.selectbox("Escolhe o objeto a regenerar:", list(ASSET_RECIPES.keys()), label_visibility="collapsed")
            if st.button(f"🎯 Regenerar {asset_to_fix}", use_container_width=True):
                with st.spinner(f"A pintar o {asset_to_fix}..."):
                    try:
                        generate_single_asset(tema_mundo, asset_to_fix)
                        st.success(f"✅ {asset_to_fix} gerado com sucesso!")
                    except Exception as e:
                        st.error(f"⚠️ Operação Abortada: {str(e)}")

        st.divider()
        st.subheader("🖼️ Galeria de Assets Atuais")

        def show_img(title, path):
            if os.path.exists(path):
                st.image(path, caption=title, use_container_width=True)
            else:
                st.info(f"❌ {title} não encontrado.")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            show_img("Personagem (Player)", os.path.join(TEMPLATE_SPRITES, "PlayerSprite.png"))
            show_img("Chão (Floor)", os.path.join(TEMPLATE_TEXTURES, "FloorTexture.png"))
        with c2:
            show_img("Inimigo (Enemy)", os.path.join(TEMPLATE_SPRITES, "EnemySprite.png"))
            show_img("Obstáculo (Wall)", os.path.join(TEMPLATE_TEXTURES, "ObstacleTexture.png"))
        with c3:
            show_img("Meta (Goal)", os.path.join(TEMPLATE_TEXTURES, "GoalTexture.png"))
            show_img("Armadilha (Trap)", os.path.join(TEMPLATE_TEXTURES, "TrapTexture.png"))
        with c4:
            show_img("Moeda (Collectible)", os.path.join(TEMPLATE_TEXTURES, "CollectibleTexture.png"))
            show_img("Power-Up", os.path.join(TEMPLATE_TEXTURES, "PowerUpTexture.png"))