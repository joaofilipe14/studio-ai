import streamlit as st
import plotly.express as px
import json
import os
from db.evolution_logger import get_evolution_history

st.set_page_config(page_title="Studio-AI Dashboard", layout="wide")
DB_PATH = os.path.join("logs", "evolution.db")

st.title("📊 Studio-AI: Director Control")

df = get_evolution_history(DB_PATH)

if df.empty:
    st.warning("Base de dados vazia. Executa uma simulação primeiro!")
else:
    # --- BARRA LATERAL COM SELECTOR ---
    st.sidebar.header("Navegação")
    all_ids = df['id'].tolist()
    selected_id = st.sidebar.selectbox("Selecionar ID da Geração:", all_ids)

    # --- FILTRO POR MODO ---
    modos = df['game_mode'].unique().tolist()
    modo_f = st.sidebar.multiselect("Filtrar Modos:", modos, default=modos)

    # Aplicar o filtro
    df_filtered = df[df['game_mode'].isin(modo_f)]

    # Verificar se o filtro deixou a tabela vazia!
    if df_filtered.empty:
        st.warning("⚠️ Nenhum dado encontrado para o modo de jogo selecionado. Altera os filtros na barra lateral.")
    else:
        # --- MÉTRICAS ---
        latest = df_filtered.iloc[0] # O registo mais recente
        c1, c2, c3 = st.columns(3)
        c1.metric("Win Rate", f"{latest['win_rate']:.2f}")
        c2.metric("Enemy Speed", f"{latest['enemy_speed']} m/s")
        c3.metric("Obstacles", latest['obstacles_count'])

        # --- GRÁFICO DE TENDÊNCIA (AGORA COM CORES POR MODO) ---
        fig = px.line(
            df_filtered.sort_values('id'),
            x='id',
            y='win_rate',
            color='game_mode', # <--- A MÁGICA ACONTECE AQUI: Separa as linhas e dá-lhes cor!
            markers=True,
            title="Progresso da Evolução (Win Rate por Modo)",
            labels={'id': 'Geração (ID)', 'win_rate': 'Win Rate', 'game_mode': 'Modo de Jogo'}
        )

        # Atualizar o layout do gráfico para ficar mais bonito
        fig.update_layout(yaxis_range=[0, 1.1]) # Fixa o eixo Y de 0 a 1.1 para o win rate não "dançar"
        fig.add_hline(y=0.6, line_dash="dot", line_color="red", annotation_text="Min Sweet Spot (0.6)")
        fig.add_hline(y=0.8, line_dash="dot", line_color="green", annotation_text="Max Sweet Spot (0.8)")

        # Apresentar o gráfico (o parâmetro use_container_width é o standard atual do Streamlit)
        st.plotly_chart(fig, use_container_width=True)

        # --- DETALHE DA GERAÇÃO SELECIONADA ---
        st.divider()
        st.subheader(f"🔍 Detalhes da Geração #{selected_id}")

        # Garantir que o ID selecionado existe antes de mostrar
        detail_rows = df[df['id'] == selected_id]
        if not detail_rows.empty:
            detail = detail_rows.iloc[0]
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"**Relatório da IA:**\n\n{detail['ai_report']}")
            with col_b:
                st.json(json.loads(detail['genome_json']))