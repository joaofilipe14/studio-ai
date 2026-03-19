import re
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

# 1. Cria a nova rota isolada!
router = APIRouter(prefix="/ui", tags=["UI Preview"])

# Garante que o caminho para a pasta UI está correto (igual ao que tens no art.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "templates" / "ui"

@router.get("/preview/{screen_name}")
def preview_ui(screen_name: str):
    """Tradutor Mágico de UXML (Unity) para HTML (Browser)"""
    uxml_path = UI_DIR / f"{screen_name}.uxml"

    if not uxml_path.exists():
        return HTMLResponse(f"<h1 style='color:white;'>Erro: Ficheiro {screen_name}.uxml não encontrado!</h1>", status_code=404)

    with open(uxml_path, "r", encoding="utf-8") as f:
        uxml = f.read()

    # ENCONTRAR E LER O FICHEIRO CSS (USS)
    css_match = re.search(r'<Style src="([^"]+)"', uxml)
    css_content = ""
    if css_match:
        css_path = UI_DIR / css_match.group(1)
        if css_path.exists():
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()

    # TRADUÇÃO DE UXML PARA HTML
    html = re.sub(r'<\?xml.*?\?>', '', uxml)
    html = re.sub(r'<ui:UXML.*?>', '<div class="unity-root" style="width: 100vw; height: 100vh; display: flex; flex-direction: column;">', html)
    html = re.sub(r'</ui:UXML>', '</div>', html)
    html = re.sub(r'<Style src=".*?" />', '', html)

    html = html.replace('<ui:VisualElement', '<div').replace('</ui:VisualElement>', '</div>')

    def replace_label(m):
        attrs = m.group(1)
        text_m = re.search(r'text="([^"]*)"', attrs)
        text = text = text_m.group(1) if text_m else ""
        attrs = re.sub(r'text="[^"]*"', '', attrs)
        return f'<div {attrs}>{text}</div>'
    html = re.sub(r'<ui:Label(.*?)(?:></ui:Label>|/>)', replace_label, html)

    def replace_button(m):
        attrs = m.group(1)
        text_m = re.search(r'text="([^"]*)"', attrs)
        text = text_m.group(1) if text_m else ""
        attrs = re.sub(r'text="[^"]*"', '', attrs)
        return f'<button {attrs} style="cursor: pointer;">{text}</button>'
    html = re.sub(r'<ui:Button(.*?)(?:></ui:Button>|/>)', replace_button, html)

    html = re.sub(r'name="([^"]*)"', r'id="\1"', html)

    # TRADUÇÃO DE USS PARA CSS
    css = css_content
    css = css.replace('-unity-font-style: bold;', 'font-weight: bold;')
    css = css.replace('-unity-text-align: middle-center;', 'display: flex; justify-content: center; align-items: center; text-align: center;')
    css = css.replace('-unity-text-align: middle-left;', 'display: flex; justify-content: flex-start; align-items: center; text-align: left;')
    css = css.replace('-unity-background-scale-mode: scale-to-fit;', 'background-size: contain; background-repeat: no-repeat; background-position: center;')
    css = css.replace('-unity-background-scale-mode: scale-and-crop;', 'background-size: cover; background-position: center;')

    def replace_resource(m):
        path = m.group(1)
        if "Sprites/" in path:
            fname = path.replace("Sprites/", "") + (".png" if not path.endswith(".png") else "")
            return f'url("http://localhost:8000/art/image/sprite/{fname}")'
        elif "Textures/" in path:
            fname = path.replace("Textures/", "") + (".png" if not path.endswith(".png") else "")
            return f'url("http://localhost:8000/art/image/texture/{fname}")'
        return 'none'
    css = re.sub(r'resource\("([^"]*)"\)', replace_resource, css)

    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background-color: #000; color: white; font-family: 'Segoe UI', sans-serif; overflow: hidden; }}
            * {{ box-sizing: border-box; }}
            {css}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """
    return HTMLResponse(content=final_html)