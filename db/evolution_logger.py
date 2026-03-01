import sqlite3
import json
import pandas as pd
import os

def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Cria a tabela com a nova coluna level_id
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS evolution (
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                                            level_id INTEGER DEFAULT 1,
                                                            game_mode TEXT,
                                                            win_rate REAL,
                                                            agent_speed REAL,
                                                            enemy_speed REAL,
                                                            obstacles_count INTEGER,
                                                            time_limit REAL,
                                                            metrics_json TEXT,
                                                            genome_json TEXT,
                                                            ai_report TEXT
                   )
                   ''')

    # MIGRATION: Tenta adicionar as colunas novas a bases de dados antigas
    try:
        cursor.execute("ALTER TABLE evolution ADD COLUMN is_human BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE evolution ADD COLUMN level_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def log_evolution_to_db(db_path: str, metrics: dict, genome: dict, report: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Extrair a ID do nível que foi evoluído
    level_id = genome.get("level_id", 1)

    # 2. 🚨 A GRANDE MUDANÇA: Procurar o relatório exato deste nível na Campanha
    level_reports = metrics.get("level_reports", [])
    specific_report = {}
    for rep in level_reports:
        if rep.get("level_id") == level_id:
            specific_report = rep
            break

    # 3. Extrair as métricas a partir do relatório isolado
    game_mode = specific_report.get("mode", genome.get("mode", "PointToPoint"))
    win_rate = specific_report.get("win_rate", 0.0)
    is_human = metrics.get("is_human", False) # is_human continua na raiz do metrics

    # 4. Dados do Genoma (mantêm-se iguais)
    agent_speed = genome.get("agent", {}).get("speed", 0.0) # Nota: Se não estiver no json, dá 0.0
    obstacles_count = genome.get("obstacles", {}).get("count", 0)
    time_limit = genome.get("rules", {}).get("timeLimit", 0.0)
    enemy_speed = genome.get("rules", {}).get("enemySpeed", 0.0)

    cursor.execute('''
                   INSERT INTO evolution
                   (level_id, game_mode, is_human, win_rate, agent_speed, enemy_speed, obstacles_count, time_limit, metrics_json, genome_json, ai_report)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ''', (
                       level_id,
                       game_mode,
                       is_human,
                       win_rate,
                       agent_speed,
                       enemy_speed,
                       obstacles_count,
                       time_limit,
                       json.dumps(metrics, ensure_ascii=False),
                       json.dumps(genome, ensure_ascii=False),
                       report
                   ))
    conn.commit()
    conn.close()

def get_evolution_history(db_path: str):
    if not os.path.exists(db_path):
        return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM evolution ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_generation_by_id(db_path: str, gen_id: int):
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM evolution WHERE id = ?"
    df = pd.read_sql_query(query, conn, params=(gen_id,))
    conn.close()
    return df