"""Рисует картинки для постов: обложку и коллаж из скриншотов.
Запуск: python3 tools/make_images.py cover OUT.png "Заголовок" "Подзаголовок" "чип1|чип2|чип3"
        python3 tools/make_images.py collage OUT.png shot1.png:Подпись shot2.png:Подпись shot3.png:Подпись
"""
import sys, base64, pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
def b64(p): return 'data:image/png;base64,' + base64.b64encode(pathlib.Path(p).read_bytes()).decode()
BG = "radial-gradient(circle at 26% 50%, #6B3F1C 0%, #2A1A0E 52%, #140D08 100%)"
BASE = "*{box-sizing:border-box;margin:0}html,body{width:1280px;height:720px;overflow:hidden;font-family:Inter,'Noto Color Emoji',sans-serif;color:#fff;background:%s}" % BG
def cover(title, sub, chips):
    ch = ''.join(f'<span class="chip">{c}</span>' for c in chips if c)
    return f"""<style>{BASE}
.wrap{{display:flex;align-items:center;height:100%;padding:0 70px 0 50px;gap:40px}}
.logo{{width:520px;height:520px;flex:none;filter:drop-shadow(0 20px 40px rgba(0,0,0,.5))}}
.k{{font-size:22px;letter-spacing:4px;color:#F0B550;font-weight:700;text-transform:uppercase}}
h1{{font-size:78px;line-height:1.02;font-weight:900;margin:14px 0 18px;letter-spacing:-1.5px}}
p{{font-size:30px;line-height:1.3;color:#EAD7C2}}
.chips{{display:flex;flex-wrap:wrap;gap:12px;margin-top:30px}}
.chip{{font-size:24px;padding:10px 18px;border-radius:999px;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.14)}}
.url{{position:absolute;right:56px;bottom:34px;font-size:20px;color:#B39A84}}</style>
<div class="wrap"><img class="logo" src="{b64(ROOT/'logo.png')}"><div><div class="k">Новости Калометра</div><h1>{title}</h1><p>{sub}</p><div class="chips">{ch}</div></div></div>
<div class="url">fargomrglton.github.io/kakatracker</div>"""
def collage(items):
    ph = ''.join(f'<figure><img src="{b64(p)}"><figcaption>{c}</figcaption></figure>' for p, c in items)
    return f"""<style>{BASE}
.wrap{{display:flex;justify-content:center;align-items:center;gap:46px;height:100%;padding-top:6px}}
figure{{display:flex;flex-direction:column;align-items:center;gap:16px}}
img{{height:590px;border-radius:34px;border:6px solid #0E0906;box-shadow:0 24px 50px rgba(0,0,0,.55)}}
figcaption{{font-size:26px;font-weight:800;color:#F6E9DA}}
.logo{{position:absolute;left:30px;top:26px;width:96px}}</style>
<img class="logo" src="{b64(ROOT/'logo.png')}" style="height:auto;border:0;box-shadow:none;border-radius:0"><div class="wrap">{ph}</div>"""
def render(html, out):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg = b.new_page(viewport={'width':1280,'height':720}); pg.set_content(html); pg.wait_for_timeout(300)
        pg.screenshot(path=out, type='jpeg' if out.endswith('.jpg') else 'png', **({'quality': 90} if out.endswith('.jpg') else {})); b.close()
if __name__ == '__main__':
    kind, out = sys.argv[1], sys.argv[2]
    if kind == 'cover': render(cover(sys.argv[3], sys.argv[4], sys.argv[5].split('|') if len(sys.argv) > 5 else []), out)
    else: render(collage([a.rsplit(':', 1) for a in sys.argv[3:]]), out)
