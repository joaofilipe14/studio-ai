import json
import random
from shared.planning import extract_first_json_object
from shared.ollama_client import chat

# ==========================================
# 🚨 CURVA DE DIFICULDADE (Game Design)
# ==========================================
def get_target_win_rate(level_id: int, is_human: bool) -> tuple[float, float]:
    """Define a margem de vitória ideal com base no nível atual.
       Quanto maior o nível, menor o win_rate exigido (o jogo fica mais difícil)."""
    if is_human:
        if level_id <= 2: return 0.90, 1.00   # Tutorial (Quase impossível perder)
        if level_id <= 4: return 0.80, 0.95   # Aquecimento
        if level_id <= 7: return 0.60, 0.80   # Desafio (Começa a suar)
        return 0.40, 0.60                     # Bosses (Vai morrer algumas vezes)
    else:
        # Bot precisa de uma margem mais apertada para o forçar a desenhar níveis precisos
        if level_id <= 2: return 0.85, 1.00
        if level_id <= 4: return 0.70, 0.90
        if level_id <= 7: return 0.50, 0.75
        return 0.35, 0.55

def get_progressive_boundaries(level_id: int) -> dict:
    """
    CRIA A CURVA ASCENDENTE! 📈
    Limites mínimos e máximos rígidos com base no nível.
    No nível 1 a IA nunca pode colocar 15 inimigos, e no nível 10 nunca pode colocar zero.
    """
    # Base = 1 a 10 (onde 1 é muito fácil e 10 é pesadelo)
    progression_factor = level_id / 10.0

    return {
        # Inimigos: de 0-3 (Nível 1) até 8-15 (Nível 10)
        "min_enemies": int(0 + (progression_factor * 8)),
        "max_enemies": int(3 + (progression_factor * 12)),

        # Velocidade: de 1.5-2.5 (Nível 1) até 4.0-8.0 (Nível 10)
        "min_speed": round(1.5 + (progression_factor * 2.5), 1),
        "max_speed": round(2.5 + (progression_factor * 5.5), 1),

        # Obstáculos: de 10-40 (Nível 1) até 100-250 (Nível 10)
        "min_obstacles": int(10 + (progression_factor * 90)),
        "max_obstacles": int(40 + (progression_factor * 210))
    }

def evolve_bot_genome(config: dict, metrics: dict, current_genome: dict) -> dict:
    level_id = current_genome.get("level_id", 1)

    target_min, target_max = get_target_win_rate(level_id, is_human=False)
    bounds = get_progressive_boundaries(level_id)

    level_reports = metrics.get("level_reports", [])
    my_report = next((rep for rep in level_reports if rep.get("level_id") == level_id), {})

    win_rate = my_report.get("win_rate", 0.0)
    avg_time = my_report.get("avg_time_to_goal", 0.0)
    stuck_events = my_report.get("stuck_events", 0)

    prompt = f"""
        You are an expert Game Level Designer. Your goal is to create a SMOOTH ASCENDING DIFFICULTY CURVE.
        You are evolving LEVEL {level_id} of a 10-level campaign.
        
        CURRENT LEVEL CONFIGURATION:
        - Level Genome: {json.dumps(current_genome, indent=2)}
        
        BOT SIMULATION METRICS:
        - Actual Win Rate: {win_rate:.2f} (Your target is {target_min:.2f} to {target_max:.2f})
        - Average Time to Goal: {avg_time:.1f}s
        - Stuck/Death Events: {stuck_events}
        
        STRICT PROGRESSION RULES FOR LEVEL {level_id}:
        1. You MUST keep "level_id" as {level_id}. DO NOT generate a "mode" field.
        2. NUMERICAL BOUNDARIES (CRITICAL FOR PROGRESSION):
           - "rules.enemyCount" MUST be between {bounds['min_enemies']} and {bounds['max_enemies']}.
           - "rules.enemySpeed" MUST be between {bounds['min_speed']} and {bounds['max_speed']}.
           - "obstacles.count" MUST be between {bounds['min_obstacles']} and {bounds['max_obstacles']}.
        3. IF Actual Win Rate ({win_rate:.2f}) is HIGHER than {target_max:.2f}: Make it HARDER within the boundaries.
        4. IF Actual Win Rate ({win_rate:.2f}) is LOWER than {target_min:.2f}: Make it EASIER within the boundaries.
        
        OUTPUT TASK: Return ONLY a strictly valid JSON object representing the new genome.
    """

    raw_result = _call_ollama(config, prompt, "Bot", current_genome)
    ng = raw_result.get("new_genome", raw_result)

    if isinstance(ng, dict):
        ng["level_id"] = level_id
        ng["seed"] = random.randint(1000, 99999)

        rules = ng.get("rules", {})
        rules["enemyCount"] = max(bounds['min_enemies'], min(bounds['max_enemies'], int(rules.get("enemyCount", 1))))
        rules["enemySpeed"] = max(bounds['min_speed'], min(bounds['max_speed'], float(rules.get("enemySpeed", 2.0))))
        ng["rules"] = rules

        obstacles = ng.get("obstacles", {})
        obstacles["count"] = max(bounds['min_obstacles'], min(bounds['max_obstacles'], int(obstacles.get("count", 50))))
        ng["obstacles"] = obstacles

        return {"report": f"Evolução Bot Lvl {level_id} concluída (Curva Ascendente).", "new_genome": ng}

    return {"report": "Falha ao processar.", "new_genome": current_genome}

def evolve_human_genome(config: dict, metrics: dict, current_genome: dict) -> dict:
    level_id = current_genome.get("level_id", 1)

    target_min, target_max = get_target_win_rate(level_id, is_human=True)

    bounds = get_progressive_boundaries(level_id)
    bounds['max_enemies'] = max(bounds['min_enemies'], int(bounds['max_enemies'] * 0.85))
    bounds['max_speed'] = max(bounds['min_speed'], bounds['max_speed'] * 0.85)

    level_reports = metrics.get("level_reports", [])
    my_report = next((rep for rep in level_reports if rep.get("level_id") == level_id), {})

    win_rate = my_report.get("win_rate", 0.0)
    stuck_events = my_report.get("stuck_events", 0)

    prompt = f"""
        You are an expert Game Level Designer. Your audience is a HUMAN PLAYER. 
        Your goal is to avoid frustration but maintain a progressive challenge.
        You are evolving LEVEL {level_id}.
        
        CURRENT LEVEL: {json.dumps(current_genome, indent=2)}
        
        HUMAN PLAYER METRICS:
        - Actual Win Rate: {win_rate:.2f} (Your target is {target_min:.2f} to {target_max:.2f})
        - Times Died: {stuck_events}

        STRICT PROGRESSION RULES FOR HUMAN PSYCHOLOGY:
        1. You MUST keep "level_id" as {level_id}. DO NOT generate a "mode" field.
        2. HUMAN-SAFE BOUNDARIES FOR LEVEL {level_id}:
           - "rules.enemyCount" MUST be between {bounds['min_enemies']} and {bounds['max_enemies']}.
           - "rules.enemySpeed" MUST be between {bounds['min_speed']} and {bounds['max_speed']}.
           - "obstacles.count" MUST be between {bounds['min_obstacles']} and {bounds['max_obstacles']}.
        3. IF Win Rate is {win_rate:.2f} (LOWER than {target_min:.2f}): The player is frustrated. Make it EASIER immediately!
        4. IF Win Rate is {win_rate:.2f} (HIGHER than {target_max:.2f}): The player is bored. Add slightly more enemies or speed.
        
        OUTPUT TASK: Return ONLY a strictly valid JSON object.
    """

    raw_result = _call_ollama(config, prompt, "Humano", current_genome)
    ng = raw_result.get("new_genome", raw_result)

    if isinstance(ng, dict):
        ng["level_id"] = level_id
        ng["seed"] = random.randint(1000, 99999)

        rules = ng.get("rules", {})
        rules["enemyCount"] = max(bounds['min_enemies'], min(bounds['max_enemies'], int(rules.get("enemyCount", 1))))
        rules["enemySpeed"] = max(bounds['min_speed'], min(bounds['max_speed'], float(rules.get("enemySpeed", 2.0))))
        ng["rules"] = rules

        obstacles = ng.get("obstacles", {})
        obstacles["count"] = max(bounds['min_obstacles'], min(bounds['max_obstacles'], int(obstacles.get("count", 50))))
        ng["obstacles"] = obstacles

        return {"report": f"Evolução Humana Lvl {level_id} concluída.", "new_genome": ng}

    return {"report": "Falha ao processar.", "new_genome": current_genome}

# (A função _call_ollama mantém-se exatamente igual)
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

    extracted_json = extract_first_json_object(content)
    if extracted_json is None:
        return {"report": "FALHA: O modelo não gerou JSON.", "new_genome": fallback_genome}

    return extracted_json