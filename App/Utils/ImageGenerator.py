"""Gerador de cartões para Caixinha de Perguntas.

Suporta dois modos configuráveis via IMAGE_ENGINE (config.py / runtime_config.py):

    'pillow'     — usa as imagens base de App/Assets/ como template.
                   Leve, sem deps extras. Recomendado para servidores fracos.

    'playwright' — renderiza HTML/CSS com Chromium headless (alta qualidade).
                   Mais pesado (~150-800 MB RAM). Requer: pip install playwright
                   && playwright install chromium

Funções públicas:
    criar_cartao(titulo, mensagem)   -> PIL.Image
    criar_cartao_caixinha(titulo)    -> PIL.Image
    criar_cartao_resposta(titulo, r) -> PIL.Image
    criar_story_card(titulo, msg)    -> PIL.Image
"""

import io
import os
import textwrap
import threading

from PIL import Image, ImageDraw, ImageFont

# ─── Paths de assets ────────────────────────────────────────────────

_ASSETS = os.path.join(os.path.dirname(__file__), '..', 'Assets')

def _asset(name: str) -> str:
    return os.path.normpath(os.path.join(_ASSETS, name))

_BASE_MENSAGEM  = _asset('base_mensagem.png')
_BASE_CAIXINHA  = _asset('base_caixinha.png')
_FONT_ARIAL     = _asset('arial.ttf')
_FONT_EMOJI     = _asset('NotoColorEmoji-Regular.ttf')


# ─── Playwright singleton ────────────────────────────────────────────

_pw_instance   = None   # playwright context manager
_pw_browser    = None   # Browser
_pw_lock       = threading.RLock()


def _get_browser():
    """Retorna instância singleton do browser Chromium (lazy, thread-safe)."""
    global _pw_instance, _pw_browser
    # Fast-path sem lock
    if _pw_browser:
        try:
            if _pw_browser.is_connected():
                return _pw_browser
        except Exception:
            pass
    with _pw_lock:
        if _pw_browser:
            try:
                if _pw_browser.is_connected():
                    return _pw_browser
            except Exception:
                pass
        try:
            from playwright.sync_api import sync_playwright
            _pw_instance = sync_playwright().start()
            _pw_browser  = _pw_instance.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                ],
            )
            print('[ImageGenerator] Browser Playwright inicializado.')
            return _pw_browser
        except Exception as e:
            print(f'[ImageGenerator] Playwright indisponível: {e}')
            return None


def shutdown_browser():
    """Encerra o browser Playwright gracefulmente (chamar no teardown)."""
    global _pw_instance, _pw_browser
    with _pw_lock:
        if _pw_browser:
            try:
                _pw_browser.close()
            except Exception:
                pass
            _pw_browser = None
        if _pw_instance:
            try:
                _pw_instance.stop()
            except Exception:
                pass
            _pw_instance = None


# ─── Engine selector ────────────────────────────────────────────────

def _get_engine() -> str:
    try:
        from App.Config.runtime_config import get_image_engine
        return get_image_engine()
    except Exception:
        try:
            from App.Config.config import IMAGE_ENGINE
            return IMAGE_ENGINE.lower()
        except Exception:
            return 'pillow'


# ─── Modo Pillow (base images) ───────────────────────────────────────

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Carrega a fonte Arial dos assets; fallback para default."""
    if os.path.exists(_FONT_ARIAL):
        return ImageFont.truetype(_FONT_ARIAL, size)
    return ImageFont.load_default()


def _draw_wrapped(draw: ImageDraw.Draw, text: str, pos: tuple,
                  font: ImageFont.FreeTypeFont, fill, width: int = 30,
                  line_height: int | None = None):
    """Desenha texto com quebra de linha, retorna y final."""
    x, y = pos
    lh = line_height or (font.size + 4)
    for line in textwrap.wrap(text, width=width):
        draw.text((x, y), line, fill=fill, font=font)
        y += lh
    return y


def _pillow_cartao_mensagem(titulo: str, mensagem: str) -> Image.Image:
    """Cartão de pergunta usando base_mensagem.png."""
    if not os.path.exists(_BASE_MENSAGEM):
        return _pillow_cartao_fallback(titulo, mensagem)

    img  = Image.open(_BASE_MENSAGEM).copy()
    draw = ImageDraw.Draw(img)

    # Título: branco, tamanho 20, posição original (140, 75)
    ft = _load_font(20)
    _draw_wrapped(draw, titulo, (140, 75), ft, fill=(255, 255, 255), width=30)

    # Mensagem: preto, tamanho 25, posição original (80, 200)
    fm = _load_font(25)
    _draw_wrapped(draw, mensagem, (80, 200), fm, fill=(0, 0, 0), width=30)

    return img


def _pillow_cartao_caixinha(titulo: str) -> Image.Image:
    """Cartão de divulgação usando base_caixinha.png."""
    if not os.path.exists(_BASE_CAIXINHA):
        return _pillow_cartao_fallback(titulo, 'Escreva no link abaixo ✈️', base='caixinha')

    img  = Image.open(_BASE_CAIXINHA).copy()
    draw = ImageDraw.Draw(img)

    # Título: branco, tamanho 30, posição original (40, 180)
    ft = _load_font(30)
    _draw_wrapped(draw, titulo, (40, 180), ft, fill=(255, 255, 255), width=30)

    return img


def _pillow_cartao_fallback(titulo: str, mensagem: str, base: str = 'mensagem') -> Image.Image:
    """Fallback puro (sem base image) se os assets não forem encontrados."""
    W, H = (500, 350) if base == 'mensagem' else (500, 300)
    img  = Image.new('RGB', (W, H), color=(12, 28, 55))   # fundo escuro uniforme
    draw = ImageDraw.Draw(img)
    # Gradiente sutil no corpo (tom ligeiramente diferente)
    for y in range(H // 3, H):
        r = (y - H // 3) / max(H - H // 3 - 1, 1)
        c = (int(12 + 20 * r), int(28 + 30 * r), int(55 + 40 * r))
        draw.line([(0, y), (W, y)], fill=c)

    ft = _load_font(22)
    fm = _load_font(18)
    _draw_wrapped(draw, titulo, (20, 20), ft, fill=(255, 255, 255), width=35)
    _draw_wrapped(draw, mensagem, (20, H // 3 + 20), fm, fill=(210, 220, 235), width=40)
    return img


# ─── Modo Playwright (HTML) ──────────────────────────────────────────

def _safe_html(text: str) -> str:
    return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')


def _card_html(titulo: str, corpo: str, largura: int = 500, body_min_h: int = 120) -> str:
    titulo = _safe_html((titulo or '').strip() or 'Sem título')
    corpo  = _safe_html((corpo  or '').strip() or '...')
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:transparent;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif}}
.card{{width:{largura}px;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)}}
.header{{background:linear-gradient(180deg,#0c3c8c 0%,#1e9fe6 100%);padding:24px 28px 24px 28px;min-height:90px}}
.title{{color:#fff;font-size:22px;font-weight:600;line-height:1.3;word-wrap:break-word}}
.body{{background:#0e1c37;padding:24px 28px 20px 28px;min-height:{body_min_h}px;position:relative}}
.body-text{{color:#dce6f5;font-size:18px;line-height:1.5;word-wrap:break-word;padding-right:50px}}
.send-btn{{position:absolute;bottom:14px;right:14px;width:42px;height:42px;border-radius:50%;border:2px solid #1e9fe6;background:#fff;display:flex;align-items:center;justify-content:center}}
.send-btn svg{{width:20px;height:20px;fill:#1e9fe6;transform:rotate(-30deg)}}
</style></head><body>
<div class="card">
<div class="header"><div class="title">{titulo}</div></div>
<div class="body">
<div class="body-text">{corpo}</div>
<div class="send-btn"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></div>
</div></div></body></html>'''


def _playwright_render(html: str, width: int = 500) -> Image.Image | None:
    browser = _get_browser()
    if not browser:
        return None
    page = None
    try:
        # Viewport largo e alto o suficiente para não cortar o conteúdo
        page = browser.new_page(viewport={'width': width, 'height': 2000})
        page.set_content(html, wait_until='domcontentloaded')
        page.wait_for_timeout(100)
        el = page.query_selector('.card') or page.query_selector('body')
        # Mede a altura real do elemento após o layout
        real_h = page.evaluate(
            "(el) => el.getBoundingClientRect().height", el
        )
        # Redimensiona o viewport para a altura exata, eliminando área vazia extra
        page.set_viewport_size({'width': width, 'height': max(1, int(real_h) + 2)})
        box = el.bounding_box()
        if box and box['width'] > 0 and box['height'] > 0:
            png = page.screenshot(
                type='png',
                omit_background=True,
                clip={'x': box['x'], 'y': box['y'],
                      'width': box['width'], 'height': box['height']},
            )
        else:
            png = el.screenshot(type='png', omit_background=True)
        return Image.open(io.BytesIO(png))
    except Exception as e:
        print(f'[ImageGenerator] Erro render Playwright: {e}')
        return None
    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass


# ─── Funções públicas ────────────────────────────────────────────────

def criar_cartao(titulo: str, mensagem: str) -> Image.Image:
    """Cartão de pergunta (base_mensagem.png ou HTML)."""
    if _get_engine() == 'playwright':
        img = _playwright_render(_card_html(titulo, mensagem))
        if img:
            return img
    return _pillow_cartao_mensagem(titulo, mensagem)


def criar_cartao_resposta(titulo: str, resposta: str) -> Image.Image:
    """Alias para cartão de resposta."""
    return criar_cartao(titulo, resposta)


def criar_cartao_caixinha(titulo: str) -> Image.Image:
    """Cartão de divulgação (base_caixinha.png ou HTML)."""
    if _get_engine() == 'playwright':
        img = _playwright_render(_card_html(titulo, 'Escreva no link abaixo ✈️', body_min_h=80))
        if img:
            return img
    return _pillow_cartao_caixinha(titulo)


def criar_story_card(titulo: str, mensagem: str) -> Image.Image:
    """Versão story (1080px) — sempre usa modo largo."""
    if _get_engine() == 'playwright':
        html = _card_html(titulo, mensagem, largura=1080, body_min_h=400)
        img  = _playwright_render(html, width=1080)
        if img:
            return img
    # Pillow fallback em resolução maior
    img = _pillow_cartao_mensagem(titulo, mensagem)
    return img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
