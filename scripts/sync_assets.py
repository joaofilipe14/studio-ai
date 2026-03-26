import json
import os
from pathlib import Path

# Contexto visual para a IA saber o que desenhar para cada item/efeito
ART_CONTEXT = {
    "item_life": "extra life heart, glowing red",
    "item_time_boost": "hourglass or clock, glowing cyan",
    "item_luck_boost": "four-leaf clover or dice, glowing gold",
    "item_perm_speed": "winged boot or lightning bolt, glowing neon",
    "item_trap_reduction": "shield or radar jammer, glowing purple",

    # 🚨 Efeitos da Safe Room (Agora alinhados com os novos nomes do CSS e PNG!)
    "icon-temp-speed": "energy drink or adrenaline syringe, glowing neon",
    "icon-temp-vision": "tactical flashlight or bionic eye, bright beam",
    "icon-temp-trap": "holographic map or scanner device, tech style"
}

ITEM_NEGATIVES = "photorealistic, 3d, human, character, face, messy, text, watermark"
BASE_NEGATIVES = "photorealistic, 3d, landscape, messy, text, watermark"

def to_camel_case(snake_str):
    """Converte 'item_life' para 'ItemLife'"""
    return "".join(word.capitalize() for word in snake_str.split("_"))

def main():
    script_path = Path(__file__).resolve()
    # Ajusta a pasta base consoante corras de dentro da pasta scripts ou da raiz
    base_dir = script_path.parent.parent if script_path.parent.name == "scripts" else script_path.parent

    roster_path = base_dir / "templates" / "json" / "roster.json"
    safe_room_path = base_dir / "templates" / "json" / "safe_room_items.json"
    assets_path = base_dir / "memory" / "assets_recipes.json"

    # 1. CARREGAR OS DADOS (JSONs)
    with open(roster_path, "r", encoding="utf-8") as f:
        roster = json.load(f)

    with open(safe_room_path, "r", encoding="utf-8") as f:
        safe_room = json.load(f)

    if assets_path.exists():
        try:
            with open(assets_path, "r", encoding="utf-8") as f:
                assets = json.load(f)
        except json.JSONDecodeError:
            # Se o ficheiro estiver vazio ou corrompido, recomeça do zero!
            print(f"[AVISO] O ficheiro {assets_path.name} estava vazio/corrompido. A recriar...")
            assets = {}
    else:
        assets = {}

    modified_recipes = False

    # Cabeçalho do bloco CSS que vamos gerar
    css_lines = [
        "\n/* ==========================================\n",
        "   GERADO AUTOMATICAMENTE POR SYNC_ASSETS.PY\n",
        "   ========================================== */\n"
    ]

    # ==========================================
    # 2. PROCESSAR ITENS DO COFRE (ROSTER)
    # ==========================================
    for item in roster.get("items", []):
        asset_key = item["id"]
        sprite_name = f"{to_camel_case(item['id'])}Icon" # Ex: ItemLifeIcon
        css_class = f".icon-{item['id'].replace('_', '-').lower()}" # Ex: .icon-item-life

        # Adiciona a regra de CSS para este item
        css_lines.append(f"{css_class} {{ background-image: resource(\"Sprites/{sprite_name}\"); }}\n")

        # Regista a receita para a IA gerar a imagem
        if asset_key not in assets:
            visual_desc = ART_CONTEXT.get(asset_key, f"{item['name']} icon")
            assets[asset_key] = {
                "file": f"{sprite_name}.png",
                "is_sprite": True,
                "prompt": f"pixel art sprite, {{theme}} {visual_desc}, single isolated object, game inventory icon, centered, flat lighting, isolated on pure white background",
                "negative_prompt": ITEM_NEGATIVES
            }
            modified_recipes = True

    # ==========================================
    # 3. PROCESSAR ITENS DA SAFE ROOM
    # ==========================================
    safe_room_groups = {}

    for item in safe_room.get("safeRoomItems", []):
        # A classe exata que o Unity vai pedir (ex: .icon-temp-speed-common)
        original_class = f".icon-{item['id'].replace('_', '-').lower()}"

        # Limpa o nome para saber a que grupo pertence (ex: "temp_speed")
        clean_id = item['id'].replace('_common', '').replace('_uncommon', '').replace('_rare', '')

        # O nome do ficheiro e chave (ex: "icon-temp-speed")
        sprite_name = f"icon-{clean_id.replace('_', '-').lower()}"

        # Cria o grupo se ainda não existir
        if sprite_name not in safe_room_groups:
            safe_room_groups[sprite_name] = {
                "classes": [],
                "effect_type": item["effectType"]
            }

        # Adiciona a classe (common, uncommon ou rare) à lista deste grupo
        safe_room_groups[sprite_name]["classes"].append(original_class)

    # 4. Escrever o CSS agrupado e criar as receitas
    for sprite_name, data in safe_room_groups.items():
        # Junta as 3 classes com uma vírgula e quebra de linha!
        classes_str = ",\n".join(data["classes"])
        css_rule = f"{classes_str} {{\n    background-image: resource(\"Sprites/{sprite_name}\");\n}}\n"

        if css_rule not in css_lines:
            css_lines.append(css_rule)

        # Regista a receita para a IA usando a chave base ("icon-temp-speed")
        if sprite_name not in assets:
            visual_desc = ART_CONTEXT.get(sprite_name, f"{data['effect_type']} icon")
            assets[sprite_name] = {
                "file": f"{sprite_name}.png",
                "is_sprite": True,
                "prompt": f"pixel art sprite, {{theme}} {visual_desc}, single isolated object, game inventory icon, centered, flat lighting, isolated on pure white background",
                "negative_prompt": ITEM_NEGATIVES
            }
            modified_recipes = True

    # ==========================================
    # 4. PROCESSAR CLASSES (Personagens)
    # ==========================================
    for cls in roster.get("classes", []):
        char_id = cls["id"]
        # Vai buscar o nome da sprite ao JSON (ex: ExplorerSprite)
        sprite_name = cls.get("spriteName", f"{char_id}Sprite")

        # 🚨 Cria a classe de CSS para o Cofre (ex: .icon-explorer)
        css_class = f".icon-{char_id.lower()}"
        css_rule = f"{css_class} {{ background-image: resource(\"Sprites/{sprite_name}\"); }}\n"

        # Adiciona ao nosso bloco de texto CSS gerado
        if css_rule not in css_lines:
            css_lines.append(css_rule)

        # Regista a receita para a IA
        if char_id not in assets:
            visual_desc = ART_CONTEXT.get(char_id, f"{cls['name']} character")
            assets[char_id] = {
                "file": f"{sprite_name}.png",
                "is_sprite": True,
                "prompt": f"pixel art sprite, {{theme}} {visual_desc}, top-down perspective, full body standing, isolated on pure white background",
                "negative_prompt": BASE_NEGATIVES
            }
            modified_recipes = True

    # ==========================================
    # 5. GUARDAR AS RECEITAS PARA A IA
    # ==========================================
    if modified_recipes:
        assets_path.parent.mkdir(parents=True, exist_ok=True)
        with open(assets_path, "w", encoding="utf-8") as f:
            json.dump(assets, f, indent=2, ensure_ascii=False)
        print(f"[SUCESSO] {assets_path.name} atualizado com novas receitas!")
    else:
        print(f"[INFO] {assets_path.name} já contém todos os itens.")

    # ==========================================
    # 6. INJETAR O CSS EM TODOS OS FICHEIROS UI!
    # ==========================================
    uss_files = ["HUDStyle.uss", "VaultStyle.uss", "SafeRoomStyle.uss"]

    for uss_filename in uss_files:
        uss_path = base_dir / "templates" / "ui" / uss_filename
        if uss_path.exists():
            with open(uss_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Procura a nossa marca d'água de geração automática
            start_marker = "/* ==========================================\n   GERADO AUTOMATICAMENTE POR SYNC_ASSETS.PY"

            if start_marker in content:
                # Se já existir, remove a parte velha gerada por nós no passado
                clean_content = content.split(start_marker)[0].rstrip()
            else:
                clean_content = content.rstrip()

            # Anexa o bloco novinho em folha
            final_content = clean_content + "\n" + "".join(css_lines)

            with open(uss_path, "w", encoding="utf-8") as f:
                f.write(final_content)

            print(f"[SUCESSO] Classes CSS dinâmicas injetadas em {uss_filename}!")

if __name__ == "__main__":
    main()