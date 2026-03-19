import sqlite3
import os
import pandas as pd
from datetime import datetime

def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 🚨 CORREÇÃO: O nome da tabela tem de ser 'evolution_logs' para bater certo com o INSERT!
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS evolution (
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 session_id TEXT,
                                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                 level_id INTEGER,
                                 is_human BOOLEAN,
                                 win_rate REAL,
                                 time_to_win REAL,
                                 lives_lost INTEGER,
                                 timeouts INTEGER,
                                 collected_coins INTEGER,
                                 collected_crystals INTEGER,
                                 powerups_used INTEGER,
                                 enemy_count INTEGER,
                                 enemy_speed REAL,
                                 agent_speed REAL,
                                 obstacles_count INTEGER,
                                 powerups_spawned INTEGER,
                                 traps_spawned INTEGER,
                                 report TEXT
                   )
                   ''')
    conn.commit()
    conn.close()

# 🚨 Adicionámos o 'current_roster=None' no final dos argumentos
def log_evolution_to_db(db_path, metrics, new_genome, report, is_human=False, session_id=None, current_roster=None):
    try:
        init_db(db_path)
    except Exception as e:
        print(f"[red]Erro ao inicializar BD: {e}[/red]")

    if session_id is None:
        session_id = datetime.now().strftime("Session_%Y%m%d_%H%M")

    level_id = new_genome.get("level_id", 1)

    # 1. Extrair Dados do Level Design (Genome)
    rules = new_genome.get("rules", {})
    enemy_speed = float(rules.get("enemySpeed", 0.0))
    enemy_count = int(rules.get("enemyCount", 0))
    powerups_spawned = int(rules.get("powerUpCount", 0))
    traps_spawned = int(rules.get("trapCount", 0))
    obstacles_count = int(new_genome.get("obstacles", {}).get("count", 0))

    # 🚨 1.5 Extrair a Velocidade do Jogador (Roster)
    agent_speed = 5.0
    if current_roster and "classes" in current_roster and len(current_roster["classes"]) > 0:
        agent_speed = float(current_roster["classes"][0].get("baseSpeed", 5.0))

    # 2. Extrair Dados de Performance (Metrics)
    level_reports = metrics.get("level_reports", [])
    my_report = next((rep for rep in level_reports if rep.get("level_id") == level_id), {})

    win_rate = float(my_report.get("win_rate", 0.0))
    time_to_win = float(my_report.get("time_to_win", 0.0))
    lives_lost = int(my_report.get("lives_lost", 0))
    timeouts = int(my_report.get("timeouts", 0))
    collected_coins = int(my_report.get("collected_coins", 0))
    collected_crystals = int(my_report.get("collected_crystals", 0))
    powerups_used = int(my_report.get("powerups_used", 0))

    # 3. Inserção Limpa em Colunas
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 🚨 Adicionado o 'agent_speed' na Query e nos Valores
        cursor.execute('''
                       INSERT INTO evolution
                       (session_id, level_id, is_human, win_rate, time_to_win, lives_lost, timeouts,
                        collected_coins, collected_crystals, powerups_used, enemy_count, enemy_speed,
                        agent_speed, obstacles_count, powerups_spawned, traps_spawned, report)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           session_id, level_id, is_human, win_rate, time_to_win, lives_lost, timeouts,
                           collected_coins, collected_crystals, powerups_used, enemy_count, enemy_speed,
                           agent_speed, obstacles_count, powerups_spawned, traps_spawned, report
                       ))
        conn.commit()
    except sqlite3.Error as e:
        print(f"\n[bold red]🚨 ERRO SQLITE: {e}[/bold red]\n")
    finally:
        if conn: conn.close()

def get_all_metrics_for_api(db_path):
    if not os.path.exists(db_path):
        return []

    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM evolution ORDER BY id ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'is_human' in df.columns:
        df['is_human'] = df['is_human'].astype(bool)

    return df.to_dict(orient="records")