import json
from typing import Optional
from brain.planning import extract_first_json_object
from brain.ollama_client import chat
from rich import print
import random # NOVO

def evolve_bot_genome(config: dict, metrics: dict, current_genome: dict) -> dict:
    """Diretor de IA: Focado no balanceamento matemático do Bot (Level Design puro)."""
    current_mode = current_genome.get("mode", "PointToPoint")
    level_id = current_genome.get("level_id", 1)

    min_time = level_id * 15.0
    max_time = level_id * 25.0

    win_rate = metrics.get("win_rate", 0.0)
    total_collected = metrics.get("total_collected", 0)
    target_count = current_genome.get("rules", {}).get("targetCount", 1)
    total_rounds = metrics.get("total_rounds", 1)

    collect_efficiency = (total_collected / (target_count * total_rounds)) if target_count > 0 else 0

    prompt = f"""
        You are an AI Level Designer. You are evolving the current LEVEL GENOME.
        
        CURRENT LEVEL CONFIGURATION:
        - Mode: {current_mode}
        - Level Genome: {json.dumps(current_genome, indent=2)}
        
        LATEST BOT SIMULATION METRICS:
        - Win Rate: {win_rate:.2f}
        - Total Collected Items: {total_collected}
        - Collection Efficiency: {collect_efficiency:.2f}
        - Stuck Events: {metrics.get("stuck_events", 0)}
        - Timeouts: {metrics.get("timeouts", 0)}

        STRICT EVOLUTION RULES:
        1. Keep "mode" as "{current_mode}" and "level_id" EXACTLY as {level_id}. DO NOT change them.
        2. Target Win Rate: 0.6 - 0.8 (The Sweet Spot).
        3. DYNAMIC TARGET PACING (CRITICAL): For Level {level_id}, we want rounds to last between {min_time} and {max_time} seconds. 
           - IF "avg_time_to_goal" is less than {min_time}s: The game is ending too fast! Increase "arena.halfSize", increase "obstacles.count", and increase "rules.timeLimit".
        4. NUMERICAL BOUNDARIES:
           - "rules.enemyCount" MUST be between 1 and 10.
           - "rules.powerUpCount" MUST be between 0 and 15.
           - "rules.trapCount" MUST be between 0 and 20.
           - "obstacles.count" MUST be between 100 and 300.
           - "rules.enemySpeed" MUST be between 1.0 and 6.0.
        5. IF Win Rate is 1.0: The game is BORING. Make it HARDER (increase enemies, speed, and obstacles).
        6. IF Win Rate is low (< 0.6): The game is FRUSTRATING. Make it EASIER (decrease enemies and speed).
        7. DO NOT include player variables. Only return the Level Genome structure.
        
        OUTPUT TASK:
        Return ONLY a strictly valid JSON object. 
        ⚠️ CRITICAL WARNING: DO NOT COPY THE VALUES FROM THE EXAMPLE BELOW! YOU MUST INVENT YOUR OWN NUMBERS TO FIX THE CURRENT WIN RATE!

        EXAMPLE FORMAT (CHANGE THE NUMBERS!):
        {{
          "report": "I decreased enemySpeed and enemyCount because the win rate was too low.",
          "new_genome": {{
            "level_id": {level_id},
            "mode": "{current_mode}",
            "seed": 9999,
            "arena": {{ "halfSize": 12.0, "walls": true }},
            "obstacles": {{ "count": 140, "minScale": 1.0, "maxScale": 1.5 }},
            "rules": {{ "timeLimit": 40.0, "targetCount": {target_count}, "enemyCount": 2, "enemySpeed": 2.5, "powerUpCount": 6, "trapCount": 3 }}
          }}
        }}
    """

    # Executa a IA
    result = _call_ollama(config, prompt, "Bot", current_genome)

    # 🛡️ BLINDAGEM PYTHON: Força o Nível, o Modo e uma NOVA SEMENTE!
    if "new_genome" in result:
        result["new_genome"]["level_id"] = level_id
        result["new_genome"]["mode"] = current_mode
        result["new_genome"]["seed"] = random.randint(1000, 99999) # Força a mudança do mapa!

    return result


def evolve_human_genome(config: dict, metrics: dict, current_genome: dict) -> dict:
    """Diretor de IA: Focado na psicologia e frustração do Jogador Humano."""
    current_mode = current_genome.get("mode", "PointToPoint")
    level_id = current_genome.get("level_id", 1)

    # HUMANOS PRECISAM DE MAIS TEMPO PARA EXPLORAR (Ex: Nível 1 = 15 a 35 segs)
    min_time = level_id * 15.0
    max_time = level_id * 35.0

    win_rate = metrics.get("win_rate", 0.0)
    total_collected = metrics.get("total_collected", 0)

    prompt = f"""
        You are an AI Level Designer. Your target audience is a HUMAN PLAYER.
        
        CURRENT LEVEL CONFIGURATION:
        - Mode: {current_mode}
        - Level Genome: {json.dumps(current_genome, indent=2)}
        
        HUMAN PLAYER METRICS:
        - Win Rate: {win_rate:.2f}
        - Total Collected Items: {total_collected}
        - Traps Hit: {metrics.get("traps_hit", 0)}
        - Timeouts: {metrics.get("timeouts", 0)}

        STRICT EVOLUTION RULES FOR HUMAN PSYCHOLOGY:
        1. Keep "mode" as "{current_mode}".
        2. Target Win Rate for Humans: 0.7 - 0.85 (Humans need to win to stay engaged).
        3. DYNAMIC TARGET PACING: For Level {level_id}, humans enjoy rounds lasting between {min_time} and {max_time} seconds. 
           - IF "avg_time_to_goal" is < {min_time}s: The map is too small. Increase "arena.halfSize", "obstacles.count", and "rules.timeLimit".
        4. NUMERICAL BOUNDARIES:
           - "rules.enemyCount" MUST be between 1 and 4.
           - "rules.powerUpCount" MUST be between 5 and 20.
           - "rules.trapCount" MUST be between 0 and 5.
           - "obstacles.count" MUST be between 50 and 200.
        5. IF Win Rate is 1.0 (Too Easy): Make it slightly harder.
        6. IF Win Rate is low (< 0.6) (Frustrating): Make it MUCH EASIER. Decrease enemySpeed and trapCount. Increase timeLimit generously.
        7. DO NOT include player logic (no agent stats or userControl).
        
        OUTPUT TASK:
        Return ONLY a strictly valid JSON object matching EXACTLY this nested structure:
        {{
          "report": "Analysis of human performance",
          "new_genome": {{
            "level_id": {level_id},
            "mode": "{current_mode}",
            "seed": 1234,
            "arena": {{ "halfSize": 12.0, "walls": true }},
            "obstacles": {{ "count": 100, "minScale": 1.0, "maxScale": 1.5 }},
            "rules": {{ "timeLimit": 45.0, "targetCount": 1, "enemyCount": 2, "enemySpeed": 2.5, "powerUpCount": 10, "trapCount": 1 }}
          }}
        }}
    """
    result = _call_ollama(config, prompt, "Humano", current_genome)

    # BLINDAGEM PYTHON: Força o Nível e o Modo corretos
    if "new_genome" in result:
        result["new_genome"]["level_id"] = level_id
        result["new_genome"]["mode"] = current_mode
    return result

def _call_ollama(config: dict, prompt: str, target_audience: str, fallback_genome: dict) -> dict:
    """Função auxiliar para fazer a chamada real ao Ollama e extrair o JSON de forma segura."""
    messages = [
        {"role": "system", "content": "You are a deterministic AI that outputs ONLY valid JSON. No markdown."},
        {"role": "user", "content": prompt}
    ]

    resp = chat(
        host=config["ollama"]["host"],
        model=config["ollama"]["model"],
        messages=messages,
        options={
            "temperature": 0.2, # Ainda mais baixa para forçar o rigor
            "top_p": 0.9,
            "num_ctx": 4096
        }
    )
    content = resp["message"]["content"]
    print(f"\n[bold magenta][Diretor IA - {target_audience}] Relatório de Balanceamento:[/bold magenta]\n{content}\n")

    # 🚨 BLINDAGEM CONTRA FALHAS ('NoneType' object has no attribute 'get')
    extracted_json = extract_first_json_object(content)

    if extracted_json is None:
        print("[bold red]⚠️ Aviso: O Ollama falhou na formatação do JSON. A usar o nível atual como Fallback de segurança.[/bold red]")
        return {
            "report": "FALHA DE SISTEMA: O modelo não gerou JSON válido. O nível anterior foi mantido.",
            "new_genome": fallback_genome
        }

    return extracted_json