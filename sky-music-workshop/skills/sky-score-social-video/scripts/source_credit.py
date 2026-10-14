"""Require the source score author and retain a readable cover byline."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def score_credit(data):
    source = data.get('score_source')
    if not isinstance(source, dict):
        raise ValueError('score_source.author and score_source.basis are required; ask who created the source score')
    author = source.get('author', '')
    basis = source.get('basis', '')
    author = author.strip() if isinstance(author, str) else ''
    basis = basis.strip() if isinstance(basis, str) else ''
    if not author or author.lower() in {'unknown', 'tbd', 'todo', '待确认', '待填写', '未知', '作者姓名', '原谱作者'}:
        raise ValueError('Confirm the source score author; do not guess or use a placeholder')
    if len(author) > 80 or any(ord(c) < 32 for c in author) or author.lower().startswith('by:'):
        raise ValueError('score_source.author must contain the author name only, on one line (maximum 80 characters)')
    if not basis:
        raise ValueError('score_source.basis must record user confirmation or visible source attribution')
    return {'author': author, 'basis': basis, 'text': 'by:' + author}


def credit_cover(image, data, base):
    credit = score_credit(data)
    cfg = data['score_source']
    font_name = cfg.get('font_file') or (data.get('social_cover') or {}).get('font_file')
    if any(ord(c) > 127 for c in credit['text']) and not font_name:
        raise ValueError('Non-ASCII source credit requires score_source.font_file with the matching glyphs')
    font_path = Path(font_name) if font_name else None
    if font_path is not None and not font_path.is_absolute():
        font_path = Path(base) / font_path
    canvas = image.convert('RGB').copy()
    draw = ImageDraw.Draw(canvas)
    short = min(canvas.size)
    margin = max(8, round(short * .06))
    padding = max(3, round(short * .008))
    size = max(14, round(short * .024))
    while True:
        typeface = ImageFont.truetype(str(font_path), size) if font_path else ImageFont.load_default(size=size)
        box = draw.textbbox((0, 0), credit['text'], font=typeface)
        width, height = box[2] - box[0], box[3] - box[1]
        if width + 2 * padding <= canvas.width * .70:
            break
        size -= 1
        if size < 12:
            raise ValueError('Author credit cannot fit legibly; choose a larger cover or a confirmed shorter display name')
    right, bottom = canvas.width - margin, canvas.height - margin
    left, top = right - width - 2 * padding, bottom - height - 2 * padding
    draw.rounded_rectangle((left, top, right, bottom), radius=padding, fill=(24, 34, 30))
    draw.text((left + padding - box[0], top + padding - box[1]), credit['text'], font=typeface, fill='white')
    return canvas
