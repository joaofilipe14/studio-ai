import json
from brain.planning import extract_first_json_object
from brain.ollama_client import chat
from rich import print
import random

# ==========================================
# 🚨 NOVA CURVA DE DIFICULDADE (Game Design)
# ==========================================
def get_target_win_rate(level_id: int, is_human: bool) -> tuple[float, float]:
    """Define a margem de vitória ideal com base no nível atual."""
    if is_human:
        # HUMANOS desistem se for muito frustrante
        if level_id <= 2: return 0.90, 1.00   # Tutorial (Muito Fácil)
        if level_id <= 4: return 0.80, 0.95   # Aquecimento (Fácil)
        if level_id <= 7: return 0.65, 0.85   # Desafio (Médio)
        return 0.50, 0.70                     # Bosses (Difícil)
    else:
        # BOTS são perfeitos, logo os alvos podem ser mais cruéis
        if level_id <= 2: return 0.90, 1.00   # Tutorial
        if level_id <= 4: return 0.75, 0.95   # Aquecimento
        if level_id <= 7: return 0.55, 0.80   # Desafio
        return 0.40, 0.60                     # Bosses

def evolve_bot_genome(config: dict, metrics: dict, current_genome: dict) -> dict:
    """Diretor de IA: Focado no balanceamento matemático do Bot."""
    current_mode = current_genome.get("mode", "PointToPoint")
    level_id = current_genome.get("level_id", 1)

    target_min, target_max = get_target_win_rate(level_id, is_human=False)

    # 🚨 CORREÇÃO: Extrair as métricas ESPECÍFICAS deste nível!
    level_reports = metrics.get("level_reports", [])
    my_report = {}
    for rep in level_reports:
        if rep.get("level_id") == level_id:
            my_report = rep
            break

    win_rate = my_report.get("win_rate", 0.0)
    avg_time = my_report.get("avg_time_to_goal", 0.0)
    stuck_events = my_report.get("stuck_events", 0)

    min_time = level_id * 15.0
    max_time = level_id * 25.0

    prompt = f"""
        You are an AI Level Designer. You are evolving the current LEVEL GENOME.
        
        CURRENT LEVEL CONFIGURATION:
        - Mode: {current_mode}
        - Level Genome: {json.dumps(current_genome, indent=2)}
        
        LATEST BOT SIMULATION METRICS FOR THIS LEVEL:
        - Actual Win Rate: {win_rate:.2f}
        - Average Time to Goal: {avg_time:.1f}s
        - Stuck/Death Events: {stuck_events}
        
        STRICT EVOLUTION RULES:
        1. Keep "mode" as "{current_mode}" and "level_id" EXACTLY as {level_id}.
        2. 🚨 TARGET WIN RATE FOR LEVEL {level_id}: {target_min:.2f} to {target_max:.2f}.
        3. DYNAMIC TARGET PACING: Rounds should last {min_time} to {max_time} seconds. 
        4. 🚨 NUMERICAL BOUNDARIES (DO NOT EXCEED):
           - "rules.enemyCount" MUST be between 0 and 15.
           - "rules.enemySpeed" MUST be between 1.5 and 8.0.
           - "rules.timeLimit" MUST be between 15.0 and 180.0.
           - "obstacles.count" MUST be between 10 and 300.
        5. IF Actual Win Rate ({win_rate:.2f}) is HIGHER than {target_max:.2f}: Make it HARDER (increase enemies, speed, and obstacles).
        6. IF Actual Win Rate ({win_rate:.2f}) is LOWER than {target_min:.2f}: Make it EASIER (decrease enemies significantly, decrease speed, increase timeLimit).
        7. DO NOT include player variables. Only return the Level Genome structure.
        
        OUTPUT TASK:
        Return ONLY a strictly valid JSON object. 
        {{
          "report": "I changed X because the win rate ({win_rate:.2f}) was too low.",
          "new_genome": {{ ... }}
        }}
    """

    result = _call_ollama(config, prompt, "Bot", current_genome)

    if "new_genome" in result:
        ng = result["new_genome"]
        ng["level_id"] = level_id
        ng["mode"] = current_mode
        ng["seed"] = random.randint(1000, 99999)

        # 🛡️ SAFETY CLAMPS (A Mão de Ferro do Game Designer)
        rules = ng.get("rules", {})
        # Inimigos entre 0 e 15 (nunca negativos)
        rules["enemyCount"] = max(0, min(15, int(rules.get("enemyCount", 1))))
        # Velocidade entre 1.5 e 8.0
        rules["enemySpeed"] = max(1.5, min(8.0, float(rules.get("enemySpeed", 2.0))))
        # Tempo entre 15s e 180s
        rules["timeLimit"] = max(15.0, min(180.0, float(rules.get("timeLimit", 60.0))))
        ng["rules"] = rules

        obstacles = ng.get("obstacles", {})
        # Obstáculos entre 10 e 300
        obstacles["count"] = max(10, min(300, int(obstacles.get("count", 50))))
        ng["obstacles"] = obstacles

    return result


def evolve_human_genome(config: dict, metrics: dict, current_genome: dict) -> dict:
    """Diretor de IA: Focado na psicologia do Jogador Humano."""
    current_mode = current_genome.get("mode", "PointToPoint")
    level_id = current_genome.get("level_id", 1)

    target_min, target_max = get_target_win_rate(level_id, is_human=True)

    # 🚨 CORREÇÃO: Extrair as métricas ESPECÍFICAS deste nível!
    level_reports = metrics.get("level_reports", [])
    my_report = {}
    for rep in level_reports:
        if rep.get("level_id") == level_id:
            my_report = rep
            break

    win_rate = my_report.get("win_rate", 0.0)
    stuck_events = my_report.get("stuck_events", 0)

    prompt = f"""
        You are an AI Level Designer. Your target audience is a HUMAN PLAYER.
        
        CURRENT LEVEL CONFIGURATION:
        - Mode: {current_mode}
        - Level Genome: {json.dumps(current_genome, indent=2)}
        
        HUMAN PLAYER METRICS:
        - Actual Win Rate: {win_rate:.2f}
        - Times Died: {stuck_events}

        STRICT EVOLUTION RULES FOR HUMAN PSYCHOLOGY:
        1. Keep "mode" as "{current_mode}".
        2. 🚨 TARGET WIN RATE FOR LEVEL {level_id}: {target_min:.2f} to {target_max:.2f}.
        3. 🚨 NUMERICAL BOUNDARIES (DO NOT EXCEED):
           - "rules.enemyCount" MUST be between 0 and 15.
           - "rules.enemySpeed" MUST be between 1.5 and 8.0.
           - "rules.timeLimit" MUST be between 15.0 and 180.0.
           - "obstacles.count" MUST be between 10 and 300.
        4. IF Actual Win Rate ({win_rate:.2f}) is HIGHER than {target_max:.2f} (Too Easy): Make it slightly harder.
        5. IF Actual Win Rate ({win_rate:.2f}) is LOWER than {target_min:.2f} (Frustrating): Make it MUCH EASIER. Decrease enemySpeed drastically and remove enemies.
        
        OUTPUT TASK:
        Return ONLY a strictly valid JSON object.
    """
    result = _call_ollama(config, prompt, "Humano", current_genome)

    if "new_genome" in result:
        ng = result["new_genome"]
        ng["level_id"] = level_id
        ng["mode"] = current_mode
        ng["seed"] = random.randint(1000, 99999)

        # 🛡️ SAFETY CLAMPS (A Mão de Ferro do Game Designer)
        rules = ng.get("rules", {})
        # Inimigos entre 0 e 15 (nunca negativos)
        rules["enemyCount"] = max(0, min(15, int(rules.get("enemyCount", 1))))
        # Velocidade entre 1.5 e 8.0
        rules["enemySpeed"] = max(1.5, min(8.0, float(rules.get("enemySpeed", 2.0))))
        # Tempo entre 15s e 180s
        rules["timeLimit"] = max(15.0, min(180.0, float(rules.get("timeLimit", 60.0))))
        ng["rules"] = rules

        obstacles = ng.get("obstacles", {})
        # Obstáculos entre 10 e 300
        obstacles["count"] = max(10, min(300, int(obstacles.get("count", 50))))
        ng["obstacles"] = obstacles
    return result

def _call_ollama(config: dict, prompt: str, target_audience: str, fallback_genome: dict) -> dict:
    messages = [
        {"role": "system", "content": "You are a deterministic AI that outputs ONLY valid JSON. No markdown."},
        {"role": "user", "content": prompt}
    ]

    resp = chat(
        host=config["ollama"]["host"],
        model=config["ollama"]["model"],
        messages=messages,
        options={"temperature": 0.2, "top_p": 0.9, "num_ctx": 4096}
    )
    content = resp["message"]["content"]
    print(f"\n[bold magenta][Diretor IA - {target_audience}] Relatório de Balanceamento:[/bold magenta]\n{content}\n")

    extracted_json = extract_first_json_object(content)

    if extracted_json is None:
        return {"report": "FALHA: O modelo não gerou JSON.", "new_genome": fallback_genome}

    return extracted_json