import json
from typing import Optional
from brain.planning import extract_first_json_object
from brain.ollama_client import chat
from rich import print

def evolve_bot_genome(config: dict, metrics: dict, current_genome: dict) -> Optional[dict]:
    """Diretor de IA: Focado no balanceamento matemático do Bot (QA Testing)."""
    current_mode = current_genome.get("mode", "PointToPoint")
    win_rate = metrics.get("win_rate", 0.0)
    total_collected = metrics.get("total_collected", 0)
    target_count = current_genome.get("rules", {}).get("targetCount", 1)
    total_rounds = metrics.get("total_rounds", 1)

    collect_efficiency = (total_collected / (target_count * total_rounds)) if target_count > 0 else 0

    prompt = f"""
        You are an AI Game Evolution Director.
        
        CURRENT CONFIGURATION:
        - Mode: {current_mode}
        - Genome: {json.dumps(current_genome, indent=2)}
        
        LATEST BOT SIMULATION METRICS:
        - Win Rate: {win_rate:.2f}
        - Total Collected Items: {total_collected}
        - Collection Efficiency: {collect_efficiency:.2f}
        - Stuck Events: {metrics.get("stuck_events", 0)}
        - Timeouts: {metrics.get("timeouts", 0)}

        STRICT EVOLUTION RULES:
        1. Keep "mode" as "{current_mode}".
        2. Target Win Rate: 0.6 - 0.8 (The Sweet Spot).
        3. IF Win Rate is 1.0: The game is BORING. You MUST make it significantly HARDER.
           - Increase "enemySpeed".
           - Decrease "timeLimit".
           - Increase "obstacles.count" or "trapChance".
        4. IF Win Rate is low (< 0.6): The game is FRUSTRATING. Make it EASIER.
           - Decrease "enemySpeed".
           - Increase "powerUpChance".
        5. Obstacle Scaling: To create a TRUE MAZE, "obstacles.count" must be high.
           - For a dense maze, use values between 180 and 220.
           - For a slightly open maze, use values between 120 and 150.
           - DO NOT use values below 100, or the map will be too empty.
        
        OUTPUT TASK:
        Return ONLY a JSON object with:
        {{
          "report": "Analysis of metrics and changes made",
          "new_genome": {{ ... }}
        }}
    """
    return _call_ollama(config, prompt, "Bot")

def evolve_human_genome(config: dict, metrics: dict, current_genome: dict) -> Optional[dict]:
    """Diretor de IA: Focado na psicologia e frustração do Jogador Humano."""
    current_mode = current_genome.get("mode", "PointToPoint")
    win_rate = metrics.get("win_rate", 0.0)
    total_collected = metrics.get("total_collected", 0)

    prompt = f"""Diretor de IA: Focado na psicologia e frustração do Jogador Humano."""
    current_mode = current_genome.get("mode", "PointToPoint")
    win_rate = metrics.get("win_rate", 0.0)
    total_collected = metrics.get("total_collected", 0)

    prompt = f"""
        You are an AI Game Evolution Director. Your target audience is a HUMAN PLAYER.
        
        CURRENT CONFIGURATION:
        - Mode: {current_mode}
        - Genome: {json.dumps(current_genome, indent=2)}
        
        HUMAN PLAYER METRICS:
        - Win Rate: {win_rate:.2f}
        - Total Collected Items: {total_collected}
        - Traps Hit: {metrics.get("traps_hit", 0)}
        - Timeouts: {metrics.get("timeouts", 0)}

        STRICT EVOLUTION RULES FOR HUMAN PSYCHOLOGY:
        1. Keep "mode" as "{current_mode}" and "userControl" as true.
        2. Target Win Rate for Humans: 0.7 - 0.85 (Humans need to win to stay engaged).
        3. IF Win Rate is 1.0 (Too Easy): Make it slightly harder.
           - Increase "enemySpeed" slightly.
           - Decrease "timeLimit".
        4. IF Win Rate is low (< 0.6) (Frustrating): Make it MUCH EASIER.
           - Decrease "enemySpeed" drastically (e.g., cut it in half).
           - Decrease "obstacles.count" significantly (e.g., to 15-20).
           - CRITICAL: Decrease "trapChance" to 0.05 or lower, OR change "powerUpType" to "Positive". Do NOT spawn a minefield.
           - Increase "timeLimit" generously.
        
        OUTPUT TASK:
        Return ONLY a strictly valid JSON object. 
        CRITICAL RULE: DO NOT include any inline comments (like //) inside the JSON data.
        {{
          "report": "Analysis of human performance and changes made.",
          "new_genome": {{ ... }}
        }}
    """
    return _call_ollama(config, prompt, "Humano")

def _call_ollama(config: dict, prompt: str, target_audience: str) -> Optional[dict]:
    """Função auxiliar para fazer a chamada real ao Ollama e extrair o JSON."""
    messages = [
        {"role": "system", "content": "You are a deterministic AI that outputs ONLY valid JSON. No markdown."},
        {"role": "user", "content": prompt}
    ]

    resp = chat(
        host=config["ollama"]["host"],
        model=config["ollama"]["model"],
        messages=messages,
        options={
            "temperature": 0.3, # Baixa temperatura para manter a estrutura JSON segura
            "top_p": 0.9,
            "num_ctx": 4096
        }
    )
    content = resp["message"]["content"]
    print(f"\n[bold magenta][Diretor IA - {target_audience}] Relatório de Balanceamento:[/bold magenta]\n{content}\n")
    return extract_first_json_object(content)