import sys
import os

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests

# Importações do sistema
from db.evolution_logger import get_evolution_history
from brain.art_director import (
    generate_full_theme,
    TEMPLATE_SPRITES,
    TEMPLATE_TEXTURES, generate_single_asset, ASSET_RECIPES
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

# CRIAR AS ABAS PRIMEIRO, INDEPENDENTEMENTE DA BASE DE DADOS!
tab_metrics, tab_art = st.tabs(["📈 Análise de Performance", "🎨 Estúdio de Assets"])

# ==========================================
# TAB 1: ANÁLISE DE MÉTRICAS E JSON
# ==========================================
with tab_metrics:
    st.header("Análise de Evolução e Genomas")

    if df.empty:
        st.warning("⚠️ Base de dados vazia. Executa uma simulação primeiro para veres os gráficos!")
    else:
        if 'is_human' not in df.columns:
            df['is_human'] = 0
        if 'level_id' not in df.columns:
            df['level_id'] = 1

        def extract_avg_time(row):
            try:
                metrics = json.loads(row['metrics_json'])
                level_reports = metrics.get("level_reports", [])
                for rep in level_reports:
                    if rep.get("level_id") == row['level_id']:
                        return rep.get("avg_time_to_goal", 0.0)
            except:
                return 0.0
            return 0.0

        df['avg_time'] = df.apply(extract_avg_time, axis=1)

        st.sidebar.header("🔍 Filtros de Análise")
        modos = df['game_mode'].unique().tolist()
        modo_f = st.sidebar.multiselect("Filtrar Modos:", modos, default=modos)

        niveis = sorted(df['level_id'].unique().tolist())
        nivel_f = st.sidebar.multiselect("Filtrar Níveis:", niveis, default=niveis)

        st.sidebar.subheader("Tipo de Jogador")
        mostrar_humano = st.sidebar.checkbox("Incluir jogadas do Humano", value=True)
        mostrar_bot = st.sidebar.checkbox("Incluir jogadas do Bot (QA)", value=True)

        mask = df['game_mode'].isin(modo_f) & df['level_id'].isin(nivel_f)
        player_mask = pd.Series(False, index=df.index)
        if mostrar_humano: player_mask |= (df['is_human'] == 1)
        if mostrar_bot: player_mask |= (df['is_human'] == 0)

        df_filtered = df[mask & player_mask]

        if df_filtered.empty:
            st.error("Nenhum dado para os filtros selecionados.")
        else:
            latest = df_filtered.iloc[0]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Win Rate Atual", f"{latest['win_rate']:.2f}")
            m2.metric("Tempo Médio", f"{latest['avg_time']:.1f}s")
            m3.metric("Obstáculos", latest['obstacles_count'])
            m4.metric("Modo Atual", latest['game_mode'])

            st.divider()

            df_filtered = df_filtered.copy()
            df_filtered['Legenda'] = df_filtered.apply(
                lambda row: f"Lvl {row['level_id']} - {'Humano' if row['is_human'] else 'Bot'}", axis=1
            )

            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                fig1 = px.line(df_filtered.sort_values('id'), x='id', y='win_rate', color='Legenda', markers=True, title="Evolução da Taxa de Vitória")
                fig1.update_layout(yaxis_range=[-0.1, 1.1])
                # 🚨 ATUALIZADO AQUI
                st.plotly_chart(fig1, width="stretch")

            with col_chart2:
                fig2 = px.line(df_filtered.sort_values('id'), x='id', y='avg_time', color='Legenda', markers=True, title="Tempo de Jogo (Segundos)")
                # 🚨 ATUALIZADO AQUI
                st.plotly_chart(fig2, width="stretch")

            st.divider()

            st.subheader("🔍 Inspeção Técnica e Comparação")
            all_ids = df_filtered['id'].tolist()
            selected_id = st.select_slider("Selecione um ID para inspecionar:", options=all_ids)

            detail = df[df['id'] == selected_id].iloc[0]
            genome_atual = json.loads(detail['genome_json'])
            modo_alvo = genome_atual.get("mode", detail['game_mode'])
            nivel_alvo = genome_atual.get("level_id", detail['level_id'])

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
                st.info(f"ℹ️ Esta é a primeira geração registada para o Nível {nivel_alvo}.")
                st.json(genome_atual)

            st.info(f"**Relatório da IA:** {detail['ai_report']}")

# ==========================================
# TAB 2: GERAÇÃO DE ASSETS (ART STUDIO)
# ==========================================
with tab_art:
    st.header("🎨 Geração de Pacote Visual por IA")
    tema_mundo = st.selectbox("Escolha o tema desejado:", ["Cyberpunk Neon", "Medieval Dungeon", "Alien Hive", "Frozen Cave", "Post-Apocalyptic Wasteland", "Retro 8-bit Arcade"])

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.write("**Gerar o Mundo Inteiro (Demora 2-3 min)**")
        # 🚨 ATUALIZADO AQUI
        if st.button(f"🚀 Gerar Pacote Completo", width="stretch"):
            with st.spinner(f"A Direção de Arte está a criar o pacote '{tema_mundo}'..."):
                try:
                    generate_full_theme({"theme": tema_mundo})
                    st.success(f"✅ Pacote completo gerado com sucesso!")
                except Exception as e:
                    st.error(f"⚠️ Operação Abortada: {str(e)}")

    with col_btn2:
        st.write("**Corrigir Apenas 1 Elemento (Rápido)**")
        asset_to_fix = st.selectbox("Escolhe o objeto a regenerar:", list(ASSET_RECIPES.keys()), label_visibility="collapsed")
        # 🚨 ATUALIZADO AQUI
        if st.button(f"🎯 Regenerar Selecionado", width="stretch"):
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
            # 🚨 ATUALIZADO AQUI
            st.image(path, caption=title, width="stretch")
        else:
            st.info(f"❌ {title} não gerado.")

    num_cols = 4
    cols = st.columns(num_cols)

    for index, (key, recipe) in enumerate(ASSET_RECIPES.items()):
        col = cols[index % num_cols]

        is_sprite = recipe["is_sprite"]
        folder = TEMPLATE_SPRITES if is_sprite else TEMPLATE_TEXTURES
        filepath = os.path.join(folder, recipe["file"])

        with col:
            show_img(key, filepath)