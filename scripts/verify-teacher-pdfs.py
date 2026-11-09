"""Check translated PDFs and render every page for visual review."""
from pathlib import Path
import hashlib
import json
import re
import pymupdf as fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'reports/teacher-pdf-preview'
DEST.mkdir(parents=True, exist_ok=True)
resources = json.loads((ROOT / 'reports/teacher-resources-zh.json').read_text('utf-8'))
results = []
for item in resources:
    path = ROOT / 'public' / item['local'].lstrip('/')
    source = path.parent.parent / (item['source_id'] + '.pdf')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == item['source_sha256']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
    doc = fitz.open(path)
    assert len(doc) == item['translated_pages']
    assert not doc.is_encrypted and doc.embfile_count() == 0
    assert [m['source_page'] for m in item['page_map']] == list(range(1, item['source_pages'] + 1))
    thumbnails = []
    links = 0
    for i, page in enumerate(doc):
        text = page.get_text()
        assert len(re.findall(r'[\u4e00-\u9fff]', text)) >= 12, (item['slug'], i, 'missing Chinese text')
        assert f'{i + 1} / {len(doc)}' in text
        assert '\ufffd' not in text
        for block in page.get_text('dict')['blocks']:
            if block['type'] != 0:
                continue
            for line in block['lines']:
                for span in line['spans']:
                    rect = fitz.Rect(span['bbox'])
                    assert rect.x0 >= 30 and rect.x1 <= page.rect.width - 25, (item['slug'], i, span)
                    assert rect.y0 >= 15 and rect.y1 <= page.rect.height - 15, (item['slug'], i, span)
        for link in page.get_links():
            if link['kind'] == fitz.LINK_URI:
                assert link['uri'].startswith(('https://', 'http://'))
                links += 1
        target = DEST / f"{item['slug']}-{i + 1:02}.png"
        page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False).save(target)
        thumb = Image.open(target).convert('RGB')
        thumb.thumbnail((238, 337))
        cell = Image.new('RGB', (258, 365), '#e6ebef')
        cell.paste(thumb, ((258 - thumb.width) // 2, 8))
        ImageDraw.Draw(cell).text((12, 346), f"{item['slug']} / {i + 1}", fill='#243442')
        thumbnails.append(cell)
    assert links >= item['source_links'] + 1
    sheet = Image.new('RGB', (258 * 4, 365 * ((len(doc) + 3) // 4)), 'white')
    for n, thumb in enumerate(thumbnails):
        sheet.paste(thumb, ((n % 4) * 258, (n // 4) * 365))
    sheet.save(DEST / f"{item['slug']}-contact.png")
    results.append({'slug': item['slug'], 'pages': len(doc), 'sourcePages': item['source_pages'], 'links': links, 'passed': True})
(ROOT / 'reports/teacher-pdf-validation.json').write_text(json.dumps(results, indent=2), 'utf-8')
print(json.dumps(results))
