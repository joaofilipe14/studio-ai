import json
import random
from shared.planning import extract_first_json_object
from shared.ollama_client import chat

# ==========================================
# 🚨 CURVA DE DIFICULDADE FÍSICA E PACING (Labirinto)
# ==========================================
def get_progressive_boundaries(level_id: int) -> dict:
    factor = ((level_id - 1) / 9.0) ** 1.5

    return {
        "min_enemies": int(1 + (factor * 4)),
        "max_enemies": int(3 + (factor * 12)),
        "min_speed": round(1.5 + (factor * 2.0), 1),
        "max_speed": round(2.5 + (factor * 4.0), 1),
        "min_obstacles": int(10 + (factor * 90)),
        "max_obstacles": int(40 + (factor * 210)),
        "min_traps": int(0 + (factor * 5)),
        "max_traps": int(2 + (factor * 18)),
        "min_time": 30,
        "max_time": 400,
        "min_coins": int(1 + (factor * 2)),  # Começa em 1, cresce devagar
        "max_coins": int(5 + (factor * 15))  # Nunca passa de umas 20 no Nível 10!
    }

def _get_player_context(player_save: dict, current_roster: dict) -> str:
    """Extrai o contexto do jogador para a IA ler e conta os upgrades totais"""
    loadout = player_save.get("loadout", {})
    selected_class_id = loadout.get("selectedClassID", "Desconhecido")

    class_stats = {}
    if current_roster and "classes" in current_roster:
        for char in current_roster.get("classes", []):
            if char["id"] == selected_class_id:
                class_stats = char.get("stats", {})
                break

    upgrades = player_save.get("purchasedUpgrades", {})
    total_upgrades = sum(upgrades.values()) if upgrades else 0

    return f"""
    PLAYER CHARACTER: {selected_class_id}
    - Base Speed: {class_stats.get('speed', 'Unknown')}
    - Base Lives: {class_stats.get('baseLives', 'Unknown')}
    
    TOTAL META-UPGRADES PURCHASED: {total_upgrades}
    - Extra Time Lvl: {upgrades.get('startExtraTimeLvl', 0)}
    - More PowerUps Lvl: {upgrades.get('morePowerUpsLvl', 0)}
    - Perm Speed Lvl: {upgrades.get('permSpeedLvl', 0)}
    - Trap Reduction Lvl: {upgrades.get('trapReductionLvl', 0)}
    """

def evolve_bot_genome(config: dict, metrics: dict, current_genome: dict, player_save: dict, current_roster: dict) -> dict:
    level_id = current_genome.get("level_id", 1)
    bounds = get_progressive_boundaries(level_id)

    level_reports = metrics.get("level_reports", [])
    my_report = next((rep for rep in level_reports if rep.get("level_id") == level_id), {})

    win_rate = my_report.get("win_rate", 0.0)
    lives_lost = my_report.get("lives_lost", 0)
    timeouts = my_report.get("timeouts", 0)
    collected_coins = my_report.get("collected_coins", 0)

    # 🚨 PILAR 1: A NOVA CURVA DE WIN-RATE
    if level_id <= 3:
        target_min, target_max = 0.85, 0.95
        archetype = "The Tutorial: High win rate expected (85-95%). Very easy, few enemies, generous time."
    elif level_id <= 6:
        target_min, target_max = 0.50, 0.60
        archetype = "The Friction Point: Medium difficulty (50-60%). The player should start sweating and losing some lives."
    elif level_id <= 9:
        target_min, target_max = 0.20, 0.30
        archetype = "The Gauntlet: Hard (20-30%). Brutal difficulty. Player is expected to die multiple times and rely on the shop."
    else:
        target_min, target_max = 0.05, 0.15
        archetype = "The Final Boss (Level 10): Glorious hell (5-15%). Extremely low win rate, maximum tension."

    # 🚨 PILAR 2: IMUNIDADE DE NÍVEL (Proteção contra o God Mode)
    upgrades = player_save.get("purchasedUpgrades", {})
    total_upgrades = sum(upgrades.values()) if upgrades else 0
    immunity_clause = ""

    if level_id <= 3 and total_upgrades > 2:
        immunity_clause = "CRITICAL IMMUNITY RULE: The player has multiple meta-upgrades. You MUST NOT increase the difficulty of this early level. Keep enemies and traps at the bare minimum, regardless of the high win rate."

    player_context = _get_player_context(player_save, current_roster)

    prompt = f"""
    You are an expert Game Level Designer acting as a "Dungeon Master" for a Roguelite game.
    Your goal is to SURGICALLY evolve LEVEL {level_id} for a BOT player. 
    
    {player_context}
    
    CURRENT LEVEL CONFIGURATION:
    {json.dumps(current_genome, indent=2)}
    
    BOT SIMULATION METRICS FOR THIS LEVEL:
    - Actual Win Rate: {win_rate:.2f} (Target is {target_min:.2f} to {target_max:.2f})
    - Lives Lost (Enemies/Traps): {lives_lost}
    - Timeouts: {timeouts}
    
    DESIGN ARCHETYPE FOR LEVEL {level_id}:
    {archetype}
    
    {immunity_clause}
    
    DESIGN RULES:
    1. If the player's character is SLOW (Speed < 6) and Timeouts > 0, INCREASE "rules.timeLimit".
    2. RISK VS REWARD: If you increase enemies or traps significantly, you MUST also increase "rules.targetCount" (coins).
    3. SURGICAL TWEAK: Only change variables that are causing issues (e.g., if Timeouts > 0, fix time. If Lives Lost > 0, tweak enemies/traps). Do not change everything blindly.
    4. "rules.enemyCount" bounds: {bounds['min_enemies']} to {bounds['max_enemies']}.
    5. "rules.enemySpeed" bounds: {bounds['min_speed']} to {bounds['max_speed']}.
    6. "obstacles.count" bounds: {bounds['min_obstacles']} to {bounds['max_obstacles']}.
    7. "rules.trapCount" bounds: {bounds['min_traps']} to {bounds['max_traps']}.
    8. "rules.timeLimit" bounds: {bounds['min_time']} to {bounds['max_time']}.
    9. "rules.targetCount" (Coins) bounds: {bounds['min_coins']} to {bounds['max_coins']}.
    
    OUTPUT TASK: Return ONLY a strictly valid JSON object structured EXACTLY like this:
    {{
        "new_genome": {{ ... the updated genome object ... }}
    }}
    """

    raw_result = _call_ollama(config, prompt, "Bot", current_genome)
    ng = raw_result.get("new_genome", current_genome) if isinstance(raw_result, dict) else current_genome

    return _apply_genome_bounds(ng, level_id, bounds, "Bot")

# ==========================================
# (As funções _apply_genome_bounds, evolve_human_genome, evolve_economy mantêm-se inalteradas na base, mas precisas de atualizar o evolve_human_genome para aceitar o player_save e o current_roster também se o usares)
# ==========================================
def evolve_human_genome(config: dict, metrics: dict, current_genome: dict) -> dict:
    level_id = current_genome.get("level_id", 1)
    bounds = get_progressive_boundaries(level_id)

    level_reports = metrics.get("level_reports", [])
    my_report = next((rep for rep in level_reports if rep.get("level_id") == level_id), {})

    win_rate = my_report.get("win_rate", 0.0)
    lives_lost = my_report.get("lives_lost", 0)
    timeouts = my_report.get("timeouts", 0)

    # 🚨 PILAR 1: A NOVA CURVA DE WIN-RATE (Aplicada aos Humanos)
    if level_id <= 3:
        target_min, target_max = 0.85, 0.95
        archetype = "The Tutorial: High win rate expected (85-95%). Very easy, few enemies, generous time. DO NOT overcomplicate."
        acceptable_deaths = 0 # Não queremos o humano a morrer no tutorial!
    elif level_id <= 6:
        target_min, target_max = 0.50, 0.60
        archetype = "The Friction Point: Medium difficulty (50-60%). The player should start sweating and losing some lives."
        acceptable_deaths = 1
    elif level_id <= 9:
        target_min, target_max = 0.20, 0.30
        archetype = "The Gauntlet: Hard (20-30%). Brutal difficulty. Player is expected to die multiple times and rely on the shop."
        acceptable_deaths = 3
    else:
        target_min, target_max = 0.05, 0.15
        archetype = "The Final Boss (Level 10): Glorious hell (5-15%). Extremely low win rate, maximum tension."
        acceptable_deaths = 5

    prompt = f"""
    You are an expert Game Level Designer.
    Your goal is to SURGICALLY evolve LEVEL {level_id} for a HUMAN player. 
    
    CURRENT LEVEL CONFIGURATION:
    {json.dumps(current_genome, indent=2)}
    
    HUMAN PLAYER METRICS FOR THIS LEVEL:
    - Actual Win Rate: {win_rate:.2f} (Target is {target_min:.2f} to {target_max:.2f})
    - Lives Lost (Enemies/Traps): {lives_lost}
    - Timeouts: {timeouts}
    
    DESIGN ARCHETYPE FOR LEVEL {level_id}:
    {archetype}
    
    STRICT PROGRESSION RULES:
    1. IF Win Rate is within the target range ({target_min:.2f}-{target_max:.2f}), DO NOT CHANGE difficulty significantly.
    2. IF Lives Lost > {acceptable_deaths}: The level is TOO HARD for this archetype. Decrease traps or enemy speed.
    3. SURGICAL TWEAK: Only change variables that are causing issues (e.g., if Timeouts > 0, fix time limit). Do not change everything blindly.
    4. "rules.enemyCount" bounds: {bounds['min_enemies']} to {bounds['max_enemies']}.
    5. "rules.enemySpeed" bounds: {bounds['min_speed']} to {bounds['max_speed']}.
    6. "obstacles.count" bounds: {bounds['min_obstacles']} to {bounds['max_obstacles']}.
    7. "rules.trapCount" bounds: {bounds['min_traps']} to {bounds['max_traps']}.
    8. "rules.timeLimit" bounds: {bounds['min_time']} to {bounds['max_time']}.
    9. "rules.targetCount" (Coins) bounds: {bounds['min_coins']} to {bounds['max_coins']}.
    
    OUTPUT TASK: Return ONLY a strictly valid JSON object structured EXACTLY like this:
    {{
        "new_genome": {{ ... the updated genome object ... }}
    }}
    """

    raw_result = _call_ollama(config, prompt, "Human", current_genome)
    ng = raw_result.get("new_genome", current_genome) if isinstance(raw_result, dict) else current_genome

    return _apply_genome_bounds(ng, level_id, bounds, "Human")

def _apply_genome_bounds(ng: dict, level_id: int, bounds: dict, player_type: str) -> dict:
    ng["level_id"] = level_id
    ng["seed"] = random.randint(1000, 99999)

    rules = ng.get("rules", {})
    rules["enemyCount"] = max(bounds['min_enemies'], min(bounds['max_enemies'], int(rules.get("enemyCount", 1))))
    rules["enemySpeed"] = max(bounds['min_speed'], min(bounds['max_speed'], float(rules.get("enemySpeed", 2.0))))
    rules["trapCount"] = max(bounds['min_traps'], min(bounds['max_traps'], int(rules.get("trapCount", 2))))
    rules["targetCount"] = max(bounds['min_coins'], min(bounds['max_coins'], int(rules.get("targetCount", 3))))
    ng["rules"] = rules

    obstacles = ng.get("obstacles", {})
    obstacles["count"] = max(bounds['min_obstacles'], min(bounds['max_obstacles'], int(obstacles.get("count", 50))))
    ng["obstacles"] = obstacles

    report_msg = f"Evolução {player_type} Lvl {level_id} concluída. Inimigos: {rules['enemyCount']} | Armadilhas: {rules['trapCount']}"
    return {"report": report_msg, "new_genome": ng}

def evolve_economy(config: dict, metrics: dict, player_save: dict, current_roster: dict, safe_room_data: dict) -> dict:
    current_wallet = player_save.get("wallet", {})
    total_coins = current_wallet.get("totalCoins", 0)
    time_crystals = current_wallet.get("timeCrystals", 0)

    # Agrupa os preços atuais para a IA analisar
    current_prices = {}
    for item in current_roster.get("items", []):
        current_prices[item["id"]] = item["cost"]
    for item in safe_room_data.get("safeRoomItems", []):
        current_prices[item["id"]] = item["cost"]

    prompt = f"""
    You are an expert Game Economy Balancing AI.
    
    PLAYER WEALTH:
    - Coins in bank (Used for Safe Room / In-Run): {total_coins}
    - Crystals in bank (Used for Vault / Meta-Progression): {time_crystals}
    
    CURRENT SHOP PRICES (ID -> Cost):
    {json.dumps(current_prices, indent=2)}
    
    YOUR GOAL: Prevent hyper-inflation and maintain the challenge.
    1. If the player is hoarding massive amounts of Crystals (e.g. > 500), INCREASE the prices of Vault items (item_life, item_time_boost, etc).
    2. If the player is hoarding Coins (e.g. > 200), INCREASE the prices of Safe Room items (temp_speed_common, temp_trap_rare, etc).
    3. If the player is broke, DECREASE prices slightly to avoid frustration.
    
    OUTPUT FORMAT: Return ONLY a valid JSON object representing the NEW prices EXACTLY like this:
    {{
      "updated_prices": {{
        "item_life": 160,
        "temp_speed_common": 18,
        ... (include all keys provided)
      }}
    }}
    """

    raw_result = _call_ollama(config, prompt, "Economia", {"updated_prices": current_prices})

    updated_prices = current_prices
    if isinstance(raw_result, dict) and "updated_prices" in raw_result:
        updated_prices = raw_result["updated_prices"]

    # 1. Injetar novos preços no Cofre (Roster) garantindo que não ficam a zero
    for item in current_roster.get("items", []):
        if item["id"] in updated_prices:
            item["cost"] = max(10, int(updated_prices[item["id"]]))

    # 2. Injetar novos preços na Safe Room garantindo que não ficam a zero
    for item in safe_room_data.get("safeRoomItems", []):
        if item["id"] in updated_prices:
            item["cost"] = max(5, int(updated_prices[item["id"]]))

    return {"new_roster": current_roster, "new_safe_room": safe_room_data, "report": "Economia ajustada com base na riqueza do jogador."}

def _call_ollama(config: dict, prompt: str, target_audience: str, fallback_data: dict) -> dict:
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
        return fallback_data

    return extracted_json