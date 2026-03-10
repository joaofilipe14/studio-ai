import json
import random
from rich import print

# Importações da nova pasta partilhada
from shared.planning import extract_first_json_object
from shared.ollama_client import chat

# ==========================================
# 🚨 CURVA DE DIFICULDADE (Game Design)
# ==========================================
def get_target_win_rate(level_id: int, is_human: bool) -> tuple[float, float]:
    """Define a margem de vitória ideal com base no nível atual."""
    if is_human:
        if level_id <= 2: return 0.90, 1.00   # Tutorial
        if level_id <= 4: return 0.80, 0.95   # Aquecimento
        if level_id <= 7: return 0.65, 0.85   # Desafio
        return 0.50, 0.70                     # Bosses
    else:
        if level_id <= 2: return 0.90, 1.00
        if level_id <= 4: return 0.75, 0.95
        if level_id <= 7: return 0.55, 0.80
        return 0.40, 0.60

def evolve_bot_genome(config: dict, metrics: dict, current_genome: dict) -> dict:
    """Diretor de IA: Focado no balanceamento matemático do Bot."""
    current_mode = current_genome.get("mode", "PointToPoint")
    level_id = current_genome.get("level_id", 1)

    target_min, target_max = get_target_win_rate(level_id, is_human=False)

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
        2. TARGET WIN RATE FOR LEVEL {level_id}: {target_min:.2f} to {target_max:.2f}.
        3. DYNAMIC TARGET PACING: Rounds should last {min_time} to {max_time} seconds. 
        4. NUMERICAL BOUNDARIES (DO NOT EXCEED):
           - "rules.enemyCount" MUST be between 0 and 15.
           - "rules.enemySpeed" MUST be between 1.5 and 8.0.
           - "rules.timeLimit" MUST be between 15.0 and 180.0.
           - "obstacles.count" MUST be between 10 and 300.
        5. IF Actual Win Rate ({win_rate:.2f}) is HIGHER than {target_max:.2f} (Too Easy): 
           - Make it HARDER by INCREASING "enemyCount", INCREASING "enemySpeed", DECREASING "timeLimit", or INCREASING "obstacles.count".
        6. IF Actual Win Rate ({win_rate:.2f}) is LOWER than {target_min:.2f} (Too Hard): 
           - Make it EASIER by DECREASING "enemyCount", DECREASING "enemySpeed", INCREASING "timeLimit", or DECREASING "obstacles.count".
        
        OUTPUT TASK: Return ONLY a strictly valid JSON object.
    """

    raw_result = _call_ollama(config, prompt, "Bot", current_genome)

    # 🎯 Lógica de Extração Robusta
    ng = raw_result.get("new_genome", raw_result)

    if isinstance(ng, dict) and "mode" in ng:
        # 🛡️ Blindagem de dados essenciais
        ng["level_id"] = level_id
        ng["mode"] = current_mode
        ng["seed"] = random.randint(1000, 99999)

        rules = ng.get("rules", {})
        rules["enemyCount"] = max(0, min(15, int(rules.get("enemyCount", 1))))
        rules["enemySpeed"] = max(1.5, min(8.0, float(rules.get("enemySpeed", 2.0))))
        rules["timeLimit"] = max(15.0, min(180.0, float(rules.get("timeLimit", 60.0))))
        ng["rules"] = rules

        obstacles = ng.get("obstacles", {})
        obstacles["count"] = max(10, min(300, int(obstacles.get("count", 50))))
        ng["obstacles"] = obstacles

        return {"report": "Evolução do Bot concluída.", "new_genome": ng}

    return {"report": "Falha ao processar genoma da IA.", "new_genome": current_genome}

def evolve_human_genome(config: dict, metrics: dict, current_genome: dict) -> dict:
    """Diretor de IA: Focado na psicologia do Jogador Humano."""
    current_mode = current_genome.get("mode", "PointToPoint")
    level_id = current_genome.get("level_id", 1)

    target_min, target_max = get_target_win_rate(level_id, is_human=True)

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
        2. TARGET WIN RATE FOR LEVEL {level_id}: {target_min:.2f} to {target_max:.2f}.
        3. NUMERICAL BOUNDARIES (DO NOT EXCEED):
           - "rules.enemyCount" MUST be between 0 and 15.
           - "rules.enemySpeed" MUST be between 1.5 and 8.0.
           - "rules.timeLimit" MUST be between 15.0 and 180.0.
           - "obstacles.count" MUST be between 10 and 300.
        4. IF Actual Win Rate ({win_rate:.2f}) is HIGHER than {target_max:.2f} (Too Easy): 
           - Make it HARDER by INCREASING "enemyCount", INCREASING "enemySpeed", or INCREASING "obstacles.count".
        5. IF Actual Win Rate ({win_rate:.2f}) is LOWER than {target_min:.2f} (Frustrating): 
           - Make it MUCH EASIER by DECREASING "enemyCount" (towards 0-3), DECREASING "enemySpeed" (towards 1.5-3.0), and INCREASING "timeLimit".
        
        OUTPUT TASK: Return ONLY a strictly valid JSON object.
    """

    raw_result = _call_ollama(config, prompt, "Humano", current_genome)

    # 🎯 Lógica de Extração Robusta
    ng = raw_result.get("new_genome", raw_result)

    if isinstance(ng, dict) and "mode" in ng:
        ng["level_id"] = level_id
        ng["mode"] = current_mode
        ng["seed"] = random.randint(1000, 99999)

        rules = ng.get("rules", {})
        rules["enemyCount"] = max(0, min(15, int(rules.get("enemyCount", 1))))
        rules["enemySpeed"] = max(1.5, min(8.0, float(rules.get("enemySpeed", 2.0))))
        rules["timeLimit"] = max(15.0, min(180.0, float(rules.get("timeLimit", 60.0))))
        ng["rules"] = rules

        obstacles = ng.get("obstacles", {})
        obstacles["count"] = max(10, min(300, int(obstacles.get("count", 50))))
        ng["obstacles"] = obstacles

        return {"report": "Evolução Humana concluída.", "new_genome": ng}

    return {"report": "Falha ao processar genoma da IA.", "new_genome": current_genome}

def _call_ollama(config: dict, prompt: str, target_audience: str, fallback_genome: dict) -> dict:
    """Faz a chamada ao Ollama e regista a resposta bruta para debug."""
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

    # Logs para depuração no terminal
    print("\n[bold cyan]🧠 --- RESPOSTA BRUTA DO OLLAMA (AI DIRECTOR) --- 🧠[/bold cyan]")
    print(content)
    print("[bold cyan]--------------------------------------------------------[/bold cyan]\n")

    extracted_json = extract_first_json_object(content)
    if extracted_json is None:
        return {"report": "FALHA: O modelo não gerou JSON.", "new_genome": fallback_genome}

    return extracted_json