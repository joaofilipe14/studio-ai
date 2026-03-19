import json
import os
import random

def generate_20_level_template():
    campaign = []

    for level_id in range(1, 21):
        # Níveis 1 a 10: Submundo Néon | Níveis 11 a 20: Zona Tóxica
        theme = "Submundo Neon" if level_id <= 10 else "Zona Toxica"

        # Crescimento base suave para o primeiro arranque da IA
        base_enemies = 1 + (level_id // 3)
        base_obstacles = 20 + (level_id * 10)

        level = {
            "level_id": level_id,
            "seed": random.randint(10000, 99999),
            "theme": theme,
            "arena": {
                "halfSize": 12.0 + (level_id // 5), # A arena cresce um bocadinho de 5 em 5 níveis
                "walls": True
            },
            "obstacles": {
                "count": base_obstacles,
                "minScale": 1.0,
                "maxScale": 1.5 + (level_id * 0.05)
            },
            "rules": {
                "timeLimit": 150.0 + (level_id * 5),
                "targetCount": 1 + (level_id // 4),
                "enemyCount": base_enemies,
                "enemySpeed": round(2.0 + (level_id * 0.15), 1),
                "powerUpCount": 3 + (level_id // 2),
                "powerUpType": "Mixed",
                "trapCount": level_id,
                "trapPenalty": 3.0 + (level_id * 0.1)
            }
        }
        campaign.append(level)

    # Guarda diretamente na pasta de templates
    template_path = "templates/json/level_genome.json"
    os.makedirs(os.path.dirname(template_path), exist_ok=True)

    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(campaign, f, indent=2)

    print(f"✅ Template de 20 níveis gerado com sucesso em: {template_path}")

if __name__ == "__main__":
    generate_20_level_template()