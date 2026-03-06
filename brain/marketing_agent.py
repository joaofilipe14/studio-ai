import json
import os
from brain.ollama_client import chat
from db.evolution_logger import get_evolution_history

# Caminho para o ficheiro de persistência
MARKETING_FILE = os.path.join("memory", "marketing_plan.json")

def generate_weekly_marketing_plan(db_path, theme):
    """Consulta a BD e gera 7 posts baseados na performance real."""
    df = get_evolution_history(db_path)
    last_runs = df.head(3).to_dict(orient='records') if not df.empty else "Sem dados"

    dias = ["Segunda", "Terça (Imagem)", "Quarta", "Quinta", "Sexta (Vídeo)", "Sábado", "Domingo"]
    plan = []

    for dia in dias:
        post_type = "Imagem" if "Imagem" in dia else ("Vídeo" if "Vídeo" in dia else "Texto")
        prompt = f"Gera um post de {post_type} para {dia}. Tema: {theme}. Métricas: {last_runs}. Usa emojis e #StudioAI."

        try:
            response = chat(host="http://localhost:11434", model="llama3.1:8b",
                            messages=[{"role": "user", "content": prompt}],
                            options={"temperature": 0.7})
            texto = response["message"]["content"]
        except:
            texto = "Erro na geração do post."

        plan.append({
            "dia": dia,
            "tipo": post_type,
            "texto": texto,
            "reviewed": False  # 🚩 Flag para o teu review
        })

    # Guarda no ficheiro JSON para persistência
    save_marketing_plan(plan)
    return plan

def save_marketing_plan(plan):
    os.makedirs(os.path.dirname(MARKETING_FILE), exist_ok=True)
    with open(MARKETING_FILE, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=4, ensure_ascii=False)

def load_marketing_plan():
    if os.path.exists(MARKETING_FILE):
        with open(MARKETING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None