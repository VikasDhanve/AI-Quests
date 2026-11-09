"""Build Chinese teacher PDFs from reviewed translations; preserve source PDFs."""
from pathlib import Path
from io import BytesIO
from functools import partial
import hashlib
import html
import json
import re

import pymupdf as fitz
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'localization/zh_cn/teacher-resources'
OUTPUT = ROOT / 'public/ai-quests/assets/teacher-resources/zh_cn'
SCRATCH = ROOT / 'reports/teacher-pdf-images'
OUTPUT.mkdir(parents=True, exist_ok=True)
SCRATCH.mkdir(parents=True, exist_ok=True)
DOCS = [
    ('market-marshes', '1IEh-RRho8xxsUizQ9K4vAe7EbjHGWqltmFz7oPbdJBs', '集市沼泽教师指南'),
    ('dusky-dunes', '1qmiozLE0yulxZheSVNozkhuAws5yyPChuwvMaBJr92s', '暮色沙丘教师指南'),
    ('polar-peaks', '1_QCAj4aHOe76_IX1KkDHWQgrqtjgevAQanHVr5gkL2s', '极地之巅教师指南'),
    ('handbook', '1mou_3WtU0Z9A8wYMnkNpjWrAP9uUoPbUc_0sszFI_Jw', '教师手册'),
    ('pedagogy', '1WC8HAJPxWP84Fif_h7NL4zvPnm4rGN-WWVyuUuqNMCg', '教学理念与设计方法'),
]
pdfmetrics.registerFont(TTFont('TeacherCN', 'C:/Windows/Fonts/msyh.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('TeacherCN-Bold', 'C:/Windows/Fonts/msyhbd.ttc', subfontIndex=0))
pdfmetrics.registerFontFamily('TeacherCN', normal='TeacherCN', bold='TeacherCN-Bold')
INK = colors.HexColor('#243442')
PURPLE = colors.HexColor('#6553ac')
styles = {
    'body': ParagraphStyle('body', fontName='TeacherCN', fontSize=10.4, leading=16.4,
                           textColor=INK, wordWrap='CJK', spaceAfter=8),
    'h1': ParagraphStyle('h1', fontName='TeacherCN-Bold', fontSize=25, leading=35,
                         textColor=INK, spaceBefore=22, spaceAfter=16, wordWrap='CJK'),
    'h2': ParagraphStyle('h2', fontName='TeacherCN-Bold', fontSize=16, leading=24,
                         textColor=PURPLE, spaceBefore=8, spaceAfter=12, keepWithNext=True, wordWrap='CJK'),
    'h3': ParagraphStyle('h3', fontName='TeacherCN-Bold', fontSize=11.5, leading=18,
                         textColor=INK, spaceBefore=8, spaceAfter=6, keepWithNext=True, wordWrap='CJK'),
    'small': ParagraphStyle('small', fontName='TeacherCN', fontSize=8, leading=12,
                            textColor=colors.HexColor('#596675'), wordWrap='CJK', spaceAfter=6),
    'bullet': ParagraphStyle('bullet', fontName='TeacherCN', fontSize=10.4, leading=16.4,
                             leftIndent=12, firstLineIndent=-9, textColor=INK, wordWrap='CJK', spaceAfter=6),
}


def paragraph(text, style='body'):
    return Paragraph(html.escape(text), styles[style])


def footer(title, source_page):
    def draw(canvas, doc):
        canvas.setFillColor(INK)
        canvas.setFont('TeacherCN', 8)
        canvas.drawString(46, A4[1] - 30, 'AI Quests  /  ' + title)
        canvas.setStrokeColor(colors.HexColor('#dfe5ea'))
        canvas.line(46, 42, A4[0] - 46, 42)
        canvas.setFillColor(colors.HexColor('#596675'))
        canvas.drawString(46, 28, f'本地简体中文译本  ·  对照原文第{source_page}页' if source_page else '原始资料链接')
    return draw


def make_pages(flow, title, source_page):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=46, rightMargin=46,
                            topMargin=52, bottomMargin=56, title=title)
    doc.build(flow, onFirstPage=footer(title, source_page), onLaterPages=footer(title, source_page),
              canvasmaker=partial(Canvas, invariant=1))
    return fitz.open(stream=buffer.getvalue(), filetype='pdf')


def figures(page, slug, source_page):
    result, seen = [], set()
    for info in page.get_image_info(xrefs=True):
        rect = fitz.Rect(info['bbox'])
        xref = info['xref']
        if not xref or xref in seen or rect.width < 65 or rect.height < 48:
            continue
        if rect.y0 < 45 or rect.y1 > page.rect.height - 40:
            continue
        # Cover decoration includes an empty rounded frame; retain the globe only.
        if source_page == 1 and result:
            continue
        seen.add(xref)
        target = SCRATCH / f'{slug}-{source_page}-{xref}.png'
        pix = fitz.Pixmap(page.parent, xref)
        if pix.colorspace and pix.colorspace.n > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        pix.save(target)
        image = Image(str(target))
        limit_w, limit_h = (158, 140) if source_page == 1 else (150, 70 if slug == 'polar-peaks' and source_page == 7 else 105)
        scale = min(limit_w / image.imageWidth, limit_h / image.imageHeight)
        image.drawWidth, image.drawHeight = image.imageWidth * scale, image.imageHeight * scale
        result.append(image)
    if not result:
        return []
    rows = [result[i:i + 3] for i in range(0, len(result), 3)]
    rows = [row + [''] * (3 - len(row)) for row in rows]
    table = Table(rows, colWidths=[166] * 3, hAlign='LEFT')
    table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('TOPPADDING', (0, 0), (-1, -1), 7),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
    return [Spacer(1, 8), paragraph('原版配图（保留原图；图中的游戏界面文字未重绘）', 'small'), table]


report = []
for slug, source_id, title in DOCS:
    original = OUTPUT.parent / f'{source_id}.pdf'
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    source = fitz.open(original)
    translated = (SOURCE / f'{slug}.md').read_text('utf-8')
    chunks = re.split(r'<!-- page: (\d+) -->', translated)
    pages = [(1, chunks[0])] + [(int(chunks[i]), chunks[i + 1]) for i in range(1, len(chunks), 2)]
    assert [n for n, _ in pages] == list(range(1, len(source) + 1)), f'Source page coverage: {slug}'
    output = fitz.open()
    page_map, links = [], {}
    for source_number, content in pages:
        flow = []
        for line in content.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            level = 'h1' if line.startswith('# ') else 'h2' if line.startswith('## ') else 'h3' if line.startswith('### ') else 'bullet' if line.startswith('- ') else 'body'
            value = re.sub(r'^#{1,3} |^- ', '', line)
            flow.append(paragraph(('• ' if level == 'bullet' else '') + value, level))
        if source_number == 1:
            flow += [Spacer(1, 16), paragraph('原文：Google Research 与斯坦福学习加速器配套教师资料。', 'body'),
                     paragraph('本地简体中文译本，按原文逐页对照编排，非官方中文发行版。原版内容和配图的权利归原权利人所有。', 'small')]
        flow += figures(source[source_number - 1], slug, source_number)
        start = len(output)
        fragment = make_pages(flow, title, source_number)
        output.insert_pdf(fragment)
        page_map.append({'source_page': source_number, 'translated_pages': list(range(start + 1, len(output) + 1))})
        for link in source[source_number - 1].get_links():
            url = link.get('uri', '')
            if not url.startswith(('https://', 'http://')):
                continue
            anchor = ' '.join(source[source_number - 1].get_textbox(link['from']).split())[:120]
            entry = links.setdefault(url, {'label': anchor or '原文资源链接', 'pages': []})
            if source_number not in entry['pages']:
                entry['pages'].append(source_number)
    flow = [paragraph('原始资料链接', 'h2'), paragraph('保留原文链接名称以便检索。外部网站及文档仍可能需要联网；这些链接的内容不属于本次五份译本的离线归档范围。', 'small')]
    original_url = f'https://docs.google.com/document/d/{source_id}/edit'
    flow.append(Paragraph(f'<link href="{html.escape(original_url, quote=True)}" color="#6553ac">打开本译本对应的原始文档</link>', styles['body']))
    for i, (url, info) in enumerate(links.items(), 1):
        label = html.escape(info['label'])
        pages_label = '、'.join(map(str, info['pages']))
        flow.append(Paragraph(f'{i}. 原文第{pages_label}页：<link href="{html.escape(url, quote=True)}" color="#6553ac">{label}</link>', styles['small']))
    output.insert_pdf(make_pages(flow, title, 0))
    for i, page in enumerate(output):
        page.insert_text((A4[0] - 78, A4[1] - 28), f'{i + 1} / {len(output)}', fontsize=8,
                         color=(0.35, 0.4, 0.46))
    output.set_metadata({'title': title + '（简体中文译本）', 'author': '原文：Google Research / Stanford Accelerator for Learning',
                         'subject': '本地简体中文译本；保留原图和原始资料链接', 'keywords': 'AI Quests, 教师资源, 简体中文'})
    target = OUTPUT / f'{slug}.pdf'
    output.save(target, garbage=4, deflate=True, no_new_id=True)
    assert hashlib.sha256(original.read_bytes()).hexdigest() == original_hash
    report.append({'slug': slug, 'title': title, 'source_id': source_id, 'source_sha256': original_hash,
                   'source_pages': len(source), 'translated_pages': len(output), 'page_map': page_map,
                   'source_links': len(links), 'local': '/ai-quests/assets/teacher-resources/zh_cn/' + target.name,
                   'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'bytes': target.stat().st_size})
    output.close()
    source.close()
(ROOT / 'reports/teacher-resources-zh.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
print(json.dumps([{'slug': d['slug'], 'source_pages': d['source_pages'], 'translated_pages': d['translated_pages']} for d in report]))
