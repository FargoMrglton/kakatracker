"""Публикует новые посты из posts/ в Telegram.

posts/ИМЯ.html          — текст поста (Telegram HTML: <b>, <i>, <a href>)
posts/ИМЯ.jpg|.png      — одна картинка (необязательно)
posts/ИМЯ-1.jpg, -2 ... — несколько картинок → альбом

Текст до 1024 символов идёт подписью к картинке, длиннее — отдельным сообщением после неё.
"""
import html, json, os, pathlib, re, subprocess, sys

TOKEN = os.environ.get('TOKEN', '')
CHAT = os.environ.get('CHAT', '')
DRY = os.environ.get('DRY') == '1'
API = f'https://api.telegram.org/bot{TOKEN}/'


def call(method, fields, files=()):
    args = ['curl', '-sS', API + method]
    for k, v in fields.items():
        args += ['--form-string', f'{k}={v}']
    for k, path in files:
        args += ['-F', f'{k}=@{path}']
    if DRY:
        print('DRY', method, {k: (v[:60] + '…' if len(v) > 60 else v) for k, v in fields.items()}, [f for _, f in files])
        return
    out = subprocess.run(args, capture_output=True, text=True).stdout
    if '"ok":true' not in out:
        print(f'::error::Telegram ответил на {method}: {out}')
        sys.exit(1)


def plain_len(text):
    return len(html.unescape(re.sub(r'<[^>]+>', '', text)).encode('utf-16-le')) // 2  # Telegram считает в UTF-16


def images_for(post):
    stem, folder = post.stem, post.parent
    found = [p for p in folder.iterdir()
             if p.suffix.lower() in ('.jpg', '.jpeg', '.png')
             and (p.stem == stem or re.fullmatch(re.escape(stem) + r'-\d+', p.stem))]
    return sorted(found, key=lambda p: (len(p.stem), p.stem))


def publish(post):
    text = post.read_text(encoding='utf-8').strip()
    imgs = images_for(post)
    fits = plain_len(text) <= 1024
    base = {'chat_id': CHAT}
    print(f'→ {post.name}: {len(imgs)} картинок, {plain_len(text)} символов')
    if not imgs:
        call('sendMessage', {**base, 'text': text, 'parse_mode': 'HTML'})
        return
    if len(imgs) == 1:
        fields = {**base, 'parse_mode': 'HTML'}
        if fits:
            fields['caption'] = text
        call('sendPhoto', fields, [('photo', imgs[0])])
    else:
        media = []
        for i, _ in enumerate(imgs[:10]):
            m = {'type': 'photo', 'media': f'attach://p{i}'}
            if i == 0 and fits:
                m.update(caption=text, parse_mode='HTML')
            media.append(m)
        call('sendMediaGroup', {**base, 'media': json.dumps(media, ensure_ascii=False)},
             [(f'p{i}', p) for i, p in enumerate(imgs[:10])])
    if not fits:
        call('sendMessage', {**base, 'text': text, 'parse_mode': 'HTML',
                             'link_preview_options': json.dumps({'is_disabled': True})})


if __name__ == '__main__':
    if not DRY and (not TOKEN or not CHAT):
        print('::error::Не заданы секреты TELEGRAM_TOKEN и TELEGRAM_CHAT')
        sys.exit(1)
    posts = [pathlib.Path(p) for p in sys.argv[1:] if p.endswith('.html')]
    if not posts:
        print('Новых постов нет')
    for p in sorted(posts):
        publish(p)
