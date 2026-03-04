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
import queue
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


# ─── Playwright worker thread dedicado ──────────────────────────────
#
# O Playwright sync API usa greenlets internamente. Greenlets NÃO podem
# trocar de thread OS — portanto o browser precisa ser criado, usado e
# encerrado sempre na MESMA thread. Aqui isolamos tudo num worker
# daemon que processa tarefas via fila, eliminando o erro:
#   "Cannot switch to a different thread"
#
# Outras threads chamam _playwright_render() que submete a tarefa e
# aguarda o resultado de forma bloqueante (com timeout).

_RENDER_TIMEOUT = 30  # segundos

_task_queue: queue.Queue = queue.Queue()
_worker_thread: threading.Thread | None = None
_worker_lock = threading.Lock()


def _playwright_worker_loop():
    """Loop do worker dedicado ao Playwright. Roda em daemon thread."""
    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser = pw.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--disable-software-rasterizer',
            ],
        )
        print('[ImageGenerator] Browser Playwright inicializado.')
    except Exception as e:
        print(f'[ImageGenerator] Playwright indisponível: {e}')
        # Drena a fila sinalizando falha em todas as tarefas pendentes
        while True:
            try:
                _, _, result_box, event = _task_queue.get_nowait()
                result_box.append(None)
                event.set()
            except queue.Empty:
                break
        return

    while True:
        try:
            task = _task_queue.get(timeout=5)
        except queue.Empty:
            # Verifica se o browser ainda está vivo periodicamente
            try:
                if not browser.is_connected():
                    break
            except Exception:
                break
            continue

        if task is None:
            # Sinal de encerramento
            break

        html, width, result_box, event = task
        page = None
        try:
            page = browser.new_page(viewport={'width': width, 'height': 2000})
            page.set_content(html, wait_until='domcontentloaded')
            page.wait_for_timeout(100)
            el = page.query_selector('.wrapper') or page.query_selector('.card') or page.query_selector('body')
            real_h = page.evaluate("(el) => el.getBoundingClientRect().height", el)
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
            result_box.append(Image.open(io.BytesIO(png)))
        except Exception as e:
            print(f'[ImageGenerator] Erro render Playwright: {e}')
            result_box.append(None)
        finally:
            if page:
                try:
                    page.close()
                except Exception:
                    pass
            event.set()

    # Encerramento limpo
    try:
        browser.close()
    except Exception:
        pass
    try:
        pw.stop()
    except Exception:
        pass
    print('[ImageGenerator] Browser Playwright encerrado.')


def _ensure_worker():
    """Garante que o worker thread está rodando (lazy, thread-safe)."""
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return
    with _worker_lock:
        if _worker_thread and _worker_thread.is_alive():
            return
        t = threading.Thread(target=_playwright_worker_loop, daemon=True, name='playwright-worker')
        t.start()
        _worker_thread = t


def shutdown_browser():
    """Encerra o worker Playwright gracefulmente (chamar no teardown)."""
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        _task_queue.put(None)  # sinal de encerramento
        _worker_thread.join(timeout=10)
        _worker_thread = None


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


def _apply_round_mask(img: Image.Image, mask_name: str = 'mask_mensagem',
                      radius: int = 30) -> Image.Image:
    """Aplica máscara à imagem, tornando o fundo transparente.

    Procura por ``<mask_name>.png`` em Assets/ e usa como máscara customizada
    (canal L: branco=visível, preto=transparente). Se não encontrar, gera
    geometricamente conforme o ``mask_name``:

    - ``mask_mensagem``  → rounded-rect simples
    - ``mask_caixinha``  → rounded-rect + círculo no topo centro (foto de perfil)
    - qualquer outro     → rounded-rect simples
    """
    img = img.convert('RGBA')
    W, H = img.size

    custom_mask_path = _asset(f'{mask_name}.png')
    if os.path.exists(custom_mask_path):
        mask_img = Image.open(custom_mask_path).convert('L').resize((W, H), Image.LANCZOS)
        img.putalpha(mask_img)
        return img

    # Gera máscara geometricamente
    mask = Image.new('L', (W, H), 0)
    draw_mask = ImageDraw.Draw(mask)

    if mask_name == 'mask_caixinha':
        # Círculo no topo centro (raio ≈ 12% da largura)
        cr = int(W * 0.12)                  # raio do círculo
        cx = W // 2                          # centro x
        cy = cr // 2                         # centro y (metade acima da borda superior do rect)
        rect_top = cy                        # rect começa onde o centro do círculo está
        draw_mask.rounded_rectangle(
            [0, rect_top, W - 1, H - 1],
            radius=radius,
            fill=255,
        )
        draw_mask.ellipse(
            [cx - cr, cy - cr, cx + cr, cy + cr],
            fill=255,
        )
    else:
        # Rounded-rect simples (mask_mensagem e demais)
        draw_mask.rounded_rectangle(
            [0, 0, W - 1, H - 1],
            radius=radius,
            fill=255,
        )

    img.putalpha(mask)
    return img


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

    img  = Image.open(_BASE_MENSAGEM).convert('RGBA').copy()
    draw = ImageDraw.Draw(img)

    # Título: branco, tamanho 20, posição original (140, 75)
    ft = _load_font(20)
    _draw_wrapped(draw, titulo, (140, 75), ft, fill=(255, 255, 255), width=30)

    # Mensagem: preto, tamanho 25, posição original (80, 200)
    fm = _load_font(25)
    _draw_wrapped(draw, mensagem, (80, 200), fm, fill=(0, 0, 0), width=30)

    return _apply_round_mask(img, mask_name='mask_mensagem')


def _pillow_cartao_caixinha(titulo: str) -> Image.Image:
    """Cartão de divulgação usando base_caixinha.png."""
    if not os.path.exists(_BASE_CAIXINHA):
        return _pillow_cartao_fallback(titulo, 'Escreva no link abaixo ✈️', base='caixinha')

    img  = Image.open(_BASE_CAIXINHA).convert('RGBA').copy()
    draw = ImageDraw.Draw(img)

    # Título: branco, tamanho 30, posição original (40, 180)
    ft = _load_font(30)
    _draw_wrapped(draw, titulo, (40, 180), ft, fill=(255, 255, 255), width=30)

    return _apply_round_mask(img, mask_name='mask_caixinha')


def _pillow_cartao_fallback(titulo: str, mensagem: str, base: str = 'mensagem') -> Image.Image:
    """Fallback puro (sem base image) se os assets não forem encontrados."""
    W, H = (500, 350) if base == 'mensagem' else (500, 300)
    img  = Image.new('RGBA', (W, H), (0, 0, 0, 0))  # fundo totalmente transparente
    draw = ImageDraw.Draw(img)

    # Gradiente no corpo (header + body)
    header_h = H // 3
    for y in range(header_h):
        r = y / max(header_h - 1, 1)
        c = (int(12 + 30 * r), int(60 + 100 * r), int(140 + 90 * r), 255)
        draw.line([(0, y), (W, y)], fill=c)
    for y in range(header_h, H):
        r = (y - header_h) / max(H - header_h - 1, 1)
        c = (int(12 + 20 * r), int(28 + 30 * r), int(55 + 40 * r), 255)
        draw.line([(0, y), (W, y)], fill=c)

    ft = _load_font(22)
    fm = _load_font(18)
    _draw_wrapped(draw, titulo, (20, 20), ft, fill=(255, 255, 255), width=35)
    _draw_wrapped(draw, mensagem, (20, header_h + 20), fm, fill=(210, 220, 235), width=40)
    return _apply_round_mask(img, mask_name='mask_mensagem')


# ─── Modo Playwright (HTML) ──────────────────────────────────────────

def _safe_html(text: str) -> str:
    return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')


_SEND_BTN = '''<div class="send-btn"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></div>'''

_AVATAR_SVG = '''<svg viewBox="0 0 24 24" fill="#b0b8c1"><path d="M12 12c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm0 2c-3.33 0-10 1.67-10 5v2h20v-2c0-3.33-6.67-5-10-5z"/></svg>'''

_AVATAR_RING_CSS = '''
.avatar-ring{
  display:inline-flex;align-items:center;justify-content:center;
  background:conic-gradient(#f09433,#e6683c,#dc2743,#cc2366,#bc1888,#8a3ab9,#4c68d7,#4c68d7,#3b5998,#3897f0,#3897f0,#f09433);
  border-radius:50%;padding:3px;
}
.avatar-inner{
  background:#d0d8e0;border-radius:50%;
  display:flex;align-items:center;justify-content:center;overflow:hidden;
}
.avatar-inner svg{width:70%;height:70%;}
'''


def _card_html_pergunta(titulo: str, corpo: str, largura: int = 500) -> str:
    """Card de pergunta: avatar à esquerda do header, corpo claro com texto escuro."""
    titulo = _safe_html((titulo or '').strip() or 'Sem título')
    corpo  = _safe_html((corpo  or '').strip() or '...')
    avatar_size   = max(52, largura // 9)
    font_title    = max(18, largura // 22)
    font_body     = max(16, largura // 26)
    pad_h         = max(20, largura // 20)
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:transparent;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;width:{largura}px}}
{_AVATAR_RING_CSS}
.card{{width:{largura}px;border-radius:22px;overflow:hidden}}
.header{{
  background:linear-gradient(135deg,#1565c0 0%,#1e88e5 50%,#42b0f5 100%);
  padding:{pad_h}px {pad_h}px {pad_h}px {pad_h}px;
  display:flex;align-items:center;gap:{pad_h}px;min-height:{avatar_size+pad_h*2}px
}}
.header .avatar-ring{{width:{avatar_size}px;height:{avatar_size}px;flex-shrink:0}}
.header .avatar-inner{{width:100%;height:100%}}
.title{{color:#fff;font-size:{font_title}px;font-weight:600;line-height:1.3;word-break:break-word}}
.body{{background:#f0f2f5;padding:{pad_h}px {pad_h}px {pad_h+30}px {pad_h}px;position:relative;min-height:{max(80,largura//5)}px}}
.body-text{{color:#1c1e21;font-size:{font_body}px;line-height:1.55;word-break:break-word;padding-right:{avatar_size//2}px}}
.send-btn{{position:absolute;bottom:{pad_h//2}px;right:{pad_h//2}px;width:{avatar_size-8}px;height:{avatar_size-8}px;border-radius:50%;border:2px solid #1e88e5;background:#fff;display:flex;align-items:center;justify-content:center}}
.send-btn svg{{width:48%;height:48%;fill:#1e88e5;transform:translateX(1px) rotate(-30deg)}}
</style></head><body>
<div class="card">
  <div class="header">
    <div class="avatar-ring"><div class="avatar-inner">{_AVATAR_SVG}</div></div>
    <div class="title">{titulo}</div>
  </div>
  <div class="body">
    <div class="body-text">{corpo}</div>
    {_SEND_BTN}
  </div>
</div>
</body></html>'''


def _card_html_caixinha(titulo: str, largura: int = 500) -> str:
    """Card de caixinha: avatar centralizado acima do card, header azul, corpo claro."""
    titulo      = _safe_html((titulo or '').strip() or 'Sem título')
    corpo       = _safe_html('Escreva no link abaixo')
    avatar_size = max(64, largura // 7)
    avatar_half = avatar_size // 2
    font_title  = max(18, largura // 22)
    font_body   = max(15, largura // 28)
    pad_h       = max(20, largura // 20)
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:transparent;font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;width:{largura}px}}
{_AVATAR_RING_CSS}
.wrapper{{width:{largura}px;padding-top:{avatar_half}px;position:relative}}
.avatar-wrap{{position:absolute;top:0;left:50%;transform:translateX(-50%);z-index:2}}
.avatar-ring{{width:{avatar_size}px;height:{avatar_size}px}}
.avatar-inner{{width:100%;height:100%}}
.card{{width:{largura}px;border-radius:22px;overflow:hidden;position:relative}}
.header{{
  background:linear-gradient(135deg,#1565c0 0%,#1e88e5 50%,#42b0f5 100%);
  padding:{avatar_half + pad_h}px {pad_h}px {pad_h}px {pad_h}px;
  min-height:{avatar_half + pad_h*2}px
}}
.title{{color:#fff;font-size:{font_title}px;font-weight:600;line-height:1.3;word-break:break-word}}
.body{{background:#f0f2f5;padding:{pad_h}px {pad_h}px {pad_h+30}px {pad_h}px;position:relative;min-height:{max(60,largura//6)}px}}
.body-text{{color:#555;font-size:{font_body}px;line-height:1.5;word-break:break-word;padding-right:{avatar_size//2}px}}
.send-btn{{position:absolute;bottom:{pad_h//2}px;right:{pad_h//2}px;width:{avatar_size-16}px;height:{avatar_size-16}px;border-radius:50%;border:2px solid #1e88e5;background:#fff;display:flex;align-items:center;justify-content:center}}
.send-btn svg{{width:48%;height:48%;fill:#1e88e5;transform:translateX(1px) rotate(-30deg)}}
</style></head><body>
<div class="wrapper">
  <div class="avatar-wrap"><div class="avatar-ring"><div class="avatar-inner">{_AVATAR_SVG}</div></div></div>
  <div class="card">
    <div class="header"><div class="title">{titulo}</div></div>
    <div class="body">
      <div class="body-text">{corpo}</div>
      {_SEND_BTN}
    </div>
  </div>
</div>
</body></html>'''


def _playwright_render(html: str, width: int = 500) -> Image.Image | None:
    """Submete uma tarefa de render ao worker dedicado e aguarda o resultado."""
    _ensure_worker()
    result_box: list = []
    event = threading.Event()
    _task_queue.put((html, width, result_box, event))
    finished = event.wait(timeout=_RENDER_TIMEOUT)
    if not finished:
        print('[ImageGenerator] Playwright render timeout.')
        return None
    return result_box[0] if result_box else None


# ─── Funções públicas ────────────────────────────────────────────────

def criar_cartao(titulo: str, mensagem: str) -> Image.Image:
    """Cartão de pergunta (base_mensagem.png ou HTML)."""
    if _get_engine() == 'playwright':
        img = _playwright_render(_card_html_pergunta(titulo, mensagem))
        if img:
            return img
    return _pillow_cartao_mensagem(titulo, mensagem)


def criar_cartao_resposta(titulo: str, resposta: str) -> Image.Image:
    """Alias para cartão de resposta."""
    return criar_cartao(titulo, resposta)


def criar_cartao_caixinha(titulo: str) -> Image.Image:
    """Cartão de divulgação (base_caixinha.png ou HTML)."""
    if _get_engine() == 'playwright':
        img = _playwright_render(_card_html_caixinha(titulo))
        if img:
            return img
    return _pillow_cartao_caixinha(titulo)


def criar_story_card(titulo: str, mensagem: str) -> Image.Image:
    """Versão story (1080px) — sempre usa modo largo."""
    if _get_engine() == 'playwright':
        html = _card_html_pergunta(titulo, mensagem, largura=1080)
        img  = _playwright_render(html, width=1080)
        if img:
            return img
    # Pillow fallback em resolução maior
    img = _pillow_cartao_mensagem(titulo, mensagem)
    return img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
