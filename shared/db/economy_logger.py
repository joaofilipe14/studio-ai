import sqlite3
import json

def init_economy_db(db_path: str):
    """Cria a tabela de histórico económico se ela ainda não existir."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Criamos uma tabela dedicada à economia
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS economy_history (
                                                                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                                                  session_id TEXT,
                                                                  player_coins INTEGER,
                                                                  player_crystals INTEGER,
                                                                  prices_json TEXT
                   )
                   ''')

    conn.commit()
    conn.close()

def log_economy_snapshot(db_path: str, session_id: str, player_coins: int, player_crystals: int, prices_dict: dict):
    """Injeta a 'fotografia' financeira atual na base de dados."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Convertemos o dicionário de preços para texto JSON para ser fácil de guardar na coluna
    prices_json = json.dumps(prices_dict)

    cursor.execute('''
                   INSERT INTO economy_history (session_id, player_coins, player_crystals, prices_json)
                   VALUES (?, ?, ?, ?)
                   ''', (session_id, player_coins, player_crystals, prices_json))

    conn.commit()
    conn.close()