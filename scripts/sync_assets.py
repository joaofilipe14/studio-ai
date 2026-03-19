import json
import os
from pathlib import Path

def update_uss_file(roster, assets):
    script_path = Path(__file__).resolve()
    base_dir = script_path.parent.parent if script_path.parent.name == "scripts" else script_path.parent

    uss_path = base_dir / "templates" / "ui" / "VaultStyle.uss"
    if not uss_path.exists():
        print(f"[AVISO] Ficheiro USS não encontrado em: {uss_path}. Ignorando atualização de CSS.")
        return

    with open(uss_path, "r", encoding="utf-8") as f:
        uss_content = f.read()

    new_css_lines = []

    # 1. Injetar CSS para ITENS
    for item in roster.get("items", []):
        # Ex: item_trap_reduction -> icon-item-trap-reduction
        css_class = f".icon-{item['id'].replace('_', '-').lower()}"
        # Ex: item_trap_reduction -> ItemTrapReductionIcon
        sprite_name = "".join(word.capitalize() for word in item["id"].split("_")) + "Icon"

        if css_class not in uss_content:
            new_css_lines.append(f"{css_class} {{ background-image: resource(\"Sprites/{sprite_name}\"); }}\n")

    # 2. Injetar CSS para CLASSES (Personagens)
    for cls in roster.get("classes", []):
        css_class = f".icon-{cls['id'].lower()}" # Ex: Explorer -> icon-explorer
        sprite_name = cls['spriteName']

        if css_class not in uss_content:
            new_css_lines.append(f"{css_class} {{ background-image: resource(\"Sprites/{sprite_name}\"); }}\n")

    # 3. Guardar se houver alterações
    if new_css_lines:
        with open(uss_path, "a", encoding="utf-8") as f:
            f.write("\n/* --- AUTO-GERADO PELO PYTHON --- */\n")
            f.writelines(new_css_lines)
        print(f"[CSS INJETADO] {len(new_css_lines)} novas classes adicionadas ao {uss_path.name}!")
    else:
        print(f"[CSS OK] O {uss_path.name} já tem todas as classes.")


def sync_roster_to_assets():
    script_path = Path(__file__).resolve()
    base_dir = script_path.parent.parent if script_path.parent.name == "scripts" else script_path.parent

    roster_path = base_dir / "templates" / "json" / "roster.json"
    assets_path = base_dir / "memory" / "assets_recipes.json"

    BASE_NEGATIVES = "photorealistic, realistic, 3d, isometric, perspective, landscape, scenery, shadows, gradients, messy, ugly, complex background, text, watermark"
    ITEM_NEGATIVES = f"{BASE_NEGATIVES}, human, person, character, face, eyes, arms, legs, male, female, body, hand holding object"

    ART_CONTEXT = {
        "item_life": "mechanical glowing red heart, tech-medical device",
        "item_time_boost": "futuristic digital stopwatch, glowing cyan display",
        "item_luck_boost": "holographic microchip with a neon clover symbol",
        "item_perm_speed": "industrial energy drink can, pink neon labels, 'DRINK' text",
        "item_trap_reduction": "futuristic square metal jammer box, thick short antennas, glowing green lights, heavy machinery object, completely inanimate",
        "Explorer": "cyberpunk explorer character, balanced gear, neon pink hair",
        "Ninja": "cyberpunk ninja runner, stealth suit, glowing visor, agile stance",
        "Tank": "heavy armored cyberpunk soldier, massive build, metallic plating"
    }

    if not roster_path.exists():
        print(f"[ERRO] Roster não encontrado: {roster_path}")
        return

    with open(roster_path, "r", encoding="utf-8") as f:
        roster = json.load(f)

    assets = json.load(open(assets_path, "r", encoding="utf-8")) if assets_path.exists() else {}
    modified = False

    # GERAR ITENS
    for item in roster.get("items", []):
        asset_key = "".join(word.capitalize() for word in item["id"].split("_"))
        if asset_key not in assets:
            visual_desc = ART_CONTEXT.get(item["id"], f"{item['name']} icon")
            assets[asset_key] = {
                "file": f"{asset_key}Icon.png",
                "is_sprite": True,
                "prompt": f"pixel art sprite, {{theme}} {visual_desc}, single isolated object, game inventory icon, centered, flat lighting, isolated on pure white background",
                "negative_prompt": ITEM_NEGATIVES
            }
            modified = True

    # GERAR PERSONAGENS
    for cls in roster.get("classes", []):
        if cls["id"] not in assets:
            visual_desc = ART_CONTEXT.get(cls["id"], f"{cls['name']} character")
            assets[cls["id"]] = {
                "file": f"{cls['spriteName']}.png",
                "is_sprite": True,
                "prompt": f"pixel art sprite, {{theme}} {visual_desc}, top-down perspective, full body standing, isolated on pure white background",
                "negative_prompt": BASE_NEGATIVES
            }
            modified = True

    if modified:
        assets_path.parent.mkdir(parents=True, exist_ok=True)
        with open(assets_path, "w", encoding="utf-8") as f:
            json.dump(assets, f, indent=2, ensure_ascii=False)
        print(f"[SUCESSO] {assets_path.name} atualizado!")
    else:
        print("[INFO] assets_recipes.json não precisou de alterações.")

    # 🚨 CHAMA A NOVA FUNÇÃO PARA ATUALIZAR O CSS
    update_uss_file(roster, assets)

if __name__ == "__main__":
    sync_roster_to_assets()