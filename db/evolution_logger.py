import sqlite3
import json
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
    game_mode = genome.get("mode", "PointToPoint")
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