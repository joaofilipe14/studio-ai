import sqlite3
import json
import pandas as pd
import os

def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS evolution (
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                                            game_mode TEXT,
                                                            win_rate REAL,
                                                            agent_speed REAL,
                                                            enemy_speed REAL,          -- ADICIONADO: Para monitorizar dificuldade
                                                            obstacles_count INTEGER,
                                                            time_limit REAL,
                                                            metrics_json TEXT,
                                                            genome_json TEXT,
                                                            ai_report TEXT
                   )
                   ''')
    conn.commit()
    conn.close()

def log_evolution_to_db(db_path: str, metrics: dict, genome: dict, report: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Extrair os valores principais
    game_mode = metrics.get("currentMode", "PointToPoint")
    win_rate = metrics.get("win_rate", 0.0)
    agent_speed = genome.get("agent", {}).get("speed", 0.0)
    obstacles_count = genome.get("obstacles", {}).get("count", 0)
    time_limit = genome.get("rules", {}).get("timeLimit", 0.0)

    # ADICIONADO: Extração da velocidade do inimigo
    enemy_speed = genome.get("rules", {}).get("enemySpeed", 0.0)

    cursor.execute('''
                   INSERT INTO evolution
                   (game_mode, win_rate, agent_speed, enemy_speed, obstacles_count, time_limit, metrics_json, genome_json, ai_report)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ''', (
                       game_mode,
                       win_rate,
                       agent_speed,
                       enemy_speed, # Inserir o novo valor
                       obstacles_count,
                       time_limit,
                       json.dumps(metrics, ensure_ascii=False),
                       json.dumps(genome, ensure_ascii=False),
                       report
                   ))
    conn.commit()
    conn.close()

def get_evolution_history(db_path: str):
    """Método que o Dashboard vai chamar para obter os dados."""
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM evolution ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_generation_by_id(db_path: str, gen_id: int):
    """Busca uma geração específica."""
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM evolution WHERE id = ?"
    df = pd.read_sql_query(query, conn, params=(gen_id,))
    conn.close()
    return df