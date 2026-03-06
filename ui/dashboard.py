import datetime

import streamlit as st
import os
import json
import requests
import pandas as pd

from brain.marketing_agent import save_marketing_plan, generate_weekly_marketing_plan, load_marketing_plan, MARKETING_FILE
# Importações das tuas lógicas de backend
from db.evolution_logger import get_evolution_history
from brain.art_director import generate_full_theme, ASSET_RECIPES, generate_single_asset, TEMPLATE_SPRITES, \
    TEMPLATE_TEXTURES
from brain.generate_audio import AUDIO_RECIPES, generate_audio_asset, MUSIC_DIR

# Configuração de Página (Deve ser a primeira linha de comandos Streamlit)
st.set_page_config(page_title="Studio-AI: Master Control", layout="wide", initial_sidebar_state="expanded")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "logs", "evolution.db")

# ==========================================
# 🗺️ BARRA DE NAVEGAÇÃO LATERAL (NAVBAR)
# ==========================================
with st.sidebar:
    st.title("🎮 Studio-AI")
    st.markdown("---")
    # O "Roteamento" aqui é feito por este seletor
    page = st.radio(
        "Navegação Principal",
        ["📈 Performance", "🎨 Estúdio de Arte", "🎵 Sonoplastia", "🚀 Marketing Hub"],
        index=0
    )

    st.markdown("---")
    st.subheader("⚙️ Status do Sistema")
    # Health Checks rápidos
    ollama = "🟢" if requests.get("http://localhost:11434/", timeout=0.1).status_code == 200 else "🔴"
    st.write(f"Diretor IA: {ollama}")

# ==========================================
# 📑 LÓGICA DE RENDERIZAÇÃO POR "ROTA"
# ==========================================

if page == "📈 Performance":
    st.title("📈 Análise de Performance e Genomas")
    df = get_evolution_history(DB_PATH)
    if df.empty:
        st.warning("Sem dados. Executa uma simulação!")
    else:
        st.write("Gráficos de Win Rate e Tempo de Jogo aqui.") # [Insere aqui a tua lógica de gráficos]

elif page == "🎨 Estúdio de Arte":
    st.title("🎨 Galeria de Texturas e Sprites")

    # --- CONTROLOS DE GERAÇÃO ---
    st.subheader("🛠️ Ferramentas de Criação")
    tema_mundo = st.selectbox("Tema do Projeto:", ["Cyberpunk Neon", "Medieval Dungeon", "Alien Hive", "Frozen Cave", "Retro 8-bit"])

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.write("**Pacote Completo**")
        if st.button("🚀 Gerar Tudo (Mundo Inteiro)", use_container_width=True):
            with st.spinner(f"A criar o pacote '{tema_mundo}'..."):
                generate_full_theme({"theme": tema_mundo}) #
                st.success("✅ Mundo gerado!")

    with col_btn2:
        st.write("**Elemento Único**")
        asset_to_fix = st.selectbox("Objeto a regenerar:", list(ASSET_RECIPES.keys())) #
        if st.button("🎯 Corrigir Apenas Este", use_container_width=True):
            with st.spinner(f"A pintar {asset_to_fix}..."):
                generate_single_asset(tema_mundo, asset_to_fix) #
                st.success(f"✅ {asset_to_fix} pronto!")

    st.divider()

    # --- GALERIA DINÂMICA ---
    ver_tipo = st.radio("Visualizar na Galeria:", ["Todos", "Sprites", "Texturas"], horizontal=True)

    # Mapeamento de pastas baseado nas variáveis importadas
    folders = []
    if ver_tipo in ["Todos", "Sprites"]: folders.append((TEMPLATE_SPRITES, "👾 Sprites e Personagens"))
    if ver_tipo in ["Todos", "Texturas"]: folders.append((TEMPLATE_TEXTURES, "🧱 Texturas de Ambiente"))

    for folder_path, label in folders:
        st.subheader(label)
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if files:
                cols = st.columns(4)
                for idx, file in enumerate(files):
                    with cols[idx % 4]:
                        full_path = os.path.join(folder_path, file)
                        st.image(full_path, caption=file, use_container_width=True)
            else:
                st.info(f"Nenhum ficheiro em {label}")
        else:
            st.error(f"Pasta não encontrada: {folder_path}")

# ==========================================
# 🎵 PÁGINA: ESTÚDIO DE SOM
# ==========================================
elif page == "🎵 Sonoplastia":
    st.title("🎵 Biblioteca de Áudio")

    # --- CONTROLOS DE ÁUDIO ---
    col_aud1, col_aud2 = st.columns(2)
    with col_aud1:
        if st.button("🎶 Gerar Orquestra Completa", use_container_width=True):
            with st.spinner("A compor..."):
                for key in AUDIO_RECIPES.keys(): #
                    generate_audio_asset("Tema Atual", key)
                st.rerun()

    with col_aud2:
        audio_target = st.selectbox("Som individual:", list(AUDIO_RECIPES.keys()))
        if st.button(f"🔊 Gerar {audio_target}", use_container_width=True):
            generate_audio_asset("Tema Atual", audio_target)
            st.rerun()

    st.divider()

    # --- PLAYBACK DINÂMICO ---
    if os.path.exists(MUSIC_DIR): #
        audio_files = [f for f in os.listdir(MUSIC_DIR) if f.endswith(('.wav', '.mp3'))]
        if audio_files:
            aud_cols = st.columns(2)
            for idx, file in enumerate(audio_files):
                with aud_cols[idx % 2]:
                    with st.container(border=True):
                        st.write(f"📄 **{file}**")
                        st.audio(os.path.join(MUSIC_DIR, file))
        else:
            st.warning("Pasta de música vazia.")

# ==========================================
# 🚀 NOVA SECÇÃO: MARKETING HUB (CALENDÁRIO)
# ==========================================
elif page == "🚀 Marketing Hub":
    st.title("🚀 Agente de Marketing & Promoção")

    # Carregar do ficheiro se não estiver na sessão
    if 'marketing_plan_data' not in st.session_state:
        st.session_state['marketing_plan_data'] = load_marketing_plan()

    if os.path.exists(MARKETING_FILE):
        mtime = os.path.getmtime(MARKETING_FILE)
        st.caption(f"📂 Memória carregada (Última edição: {datetime.fromtimestamp(mtime).strftime('%d/%m %H:%M')})")
    if st.button("🤖 Gerar Novo Plano Semanal"):
        theme = st.session_state.get('current_theme', "Cyberpunk")
        plan = generate_weekly_marketing_plan(DB_PATH, theme)
        st.session_state['marketing_plan_data'] = plan
        st.success("Novo plano gerado e guardado em logs/marketing_plan.json")

    if st.session_state['marketing_plan_data']:
        for idx, post in enumerate(st.session_state['marketing_plan_data']):
            # Cor do expander muda se já foi revisado
            label = f"✅ {post['dia']}" if post['reviewed'] else f"⏳ {post['dia']}"

            with st.expander(label):
                col_txt, col_rev = st.columns([3, 1])

                with col_txt:
                    novo_texto = st.text_area("Legenda:", post['texto'], key=f"txt_{idx}")
                    if novo_texto != post['texto']:
                        st.session_state['marketing_plan_data'][idx]['texto'] = novo_texto

                with col_rev:
                    # Sistema de Review
                    is_reviewed = st.checkbox("Aprovar Post", value=post['reviewed'], key=f"rev_{idx}")
                    st.session_state['marketing_plan_data'][idx]['reviewed'] = is_reviewed

                    if st.button("💾 Guardar", key=f"save_{idx}"):
                        save_marketing_plan(st.session_state['marketing_plan_data'])
                        st.toast("Alterações guardadas!")

        # Botão final para "Publicar" (apenas o que foi revisado)
        if st.button("🚀 Publicar Posts Aprovados"):
            aprovados = [p for p in st.session_state['marketing_plan_data'] if p['reviewed']]
            st.write(f"A publicar {len(aprovados)} posts aprovados...")
            # Aqui ligarias a uma API do Twitter/Instagram ou apenas exportarias o pack final