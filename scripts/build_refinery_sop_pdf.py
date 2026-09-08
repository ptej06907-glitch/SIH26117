from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, PageBreak, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'samples' / 'maintenance-corpus' / 'refinery_process_safety_sop_demo.txt'
OUTPUT = ROOT / 'output' / 'pdf' / 'refinery_process_safety_sop_demo.pdf'


def page_chrome(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(colors.HexColor('#0b1724'))
    canvas.rect(0, height - 16 * mm, width, 16 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#c9eee6'))
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(18 * mm, height - 10 * mm, 'SOP-RPS-001')
    canvas.setFillColor(colors.HexColor('#d7e4ed'))
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(width - 18 * mm, height - 10 * mm, 'Fictional refinery reference | Aegis test corpus')
    canvas.setStrokeColor(colors.HexColor('#dbe3eb'))
    canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    canvas.setFillColor(colors.HexColor('#66798b'))
    canvas.setFont('Helvetica', 8)
    canvas.drawString(18 * mm, 9 * mm, 'Demonstration material - verify against controlled site procedures')
    canvas.drawRightString(width - 18 * mm, 9 * mm, f'Page {doc.page}')
    canvas.restoreState()


def make_styles():
    base = getSampleStyleSheet()
    return {
        'cover_title': ParagraphStyle('CoverTitle', parent=base['Title'], fontName='Helvetica-Bold', fontSize=25, leading=30, textColor=colors.HexColor('#0b1724'), alignment=TA_CENTER, spaceAfter=12),
        'cover_sub': ParagraphStyle('CoverSub', parent=base['Normal'], fontName='Helvetica', fontSize=11, leading=16, textColor=colors.HexColor('#4b6073'), alignment=TA_CENTER, spaceAfter=8),
        'h1': ParagraphStyle('H1', parent=base['Heading1'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.HexColor('#17334b'), spaceBefore=13, spaceAfter=8),
        'h2': ParagraphStyle('H2', parent=base['Heading2'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=colors.HexColor('#2d5f87'), spaceBefore=8, spaceAfter=4),
        'body': ParagraphStyle('Body', parent=base['BodyText'], fontName='Helvetica', fontSize=9.3, leading=13.5, textColor=colors.HexColor('#263849'), spaceAfter=6),
        'small': ParagraphStyle('Small', parent=base['BodyText'], fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#52687b'), spaceAfter=5),
        'bullet': ParagraphStyle('Bullet', parent=base['BodyText'], fontName='Helvetica', fontSize=9.1, leading=13, leftIndent=13, firstLineIndent=-8, textColor=colors.HexColor('#263849'), spaceAfter=3),
        'callout': ParagraphStyle('Callout', parent=base['BodyText'], fontName='Helvetica-Bold', fontSize=9.2, leading=13.5, textColor=colors.HexColor('#7b3d32'), spaceAfter=2),
        'mono': ParagraphStyle('Mono', parent=base['Code'], fontName='Courier', fontSize=8.2, leading=11, backColor=colors.HexColor('#f2f5f7'), borderColor=colors.HexColor('#dbe3eb'), borderWidth=.5, borderPadding=6, spaceAfter=7),
    }


def p(text, style):
    # Keep the output safe for ReportLab's XML parser while retaining a small set of intentional emphasis tags.
    return Paragraph(escape(text).replace('&lt;br/&gt;', '<br/>').replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>'), style)


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = make_styles()
    doc = BaseDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=24 * mm, bottomMargin=22 * mm, title='SOP-RPS-001 Refinery Process Safety Demonstration Reference')
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    doc.addPageTemplates([PageTemplate(id='main', frames=frame, onPage=page_chrome)])
    story = []
    lines = SOURCE.read_text(encoding='utf-8').splitlines()

    story.extend([Spacer(1, 35 * mm), p('SOP-RPS-001', styles['cover_sub']), p('Refinery Process Safety, Maintenance Isolation, and Incident Response', styles['cover_title']), p('A fictional, source-grounded reference procedure for testing local incident analysis', styles['cover_sub']), Spacer(1, 10 * mm)])
    cover = Table([[p('<b>Revision</b><br/>1.0', styles['body']), p('<b>Effective date</b><br/>2026-09-08', styles['body']), p('<b>Classification</b><br/>Internal demonstration', styles['body'])]], colWidths=[doc.width / 3] * 3)
    cover.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#edf3f8')), ('BOX', (0, 0), (-1, -1), .7, colors.HexColor('#c9d7e3')), ('INNERGRID', (0, 0), (-1, -1), .4, colors.HexColor('#dbe3eb')), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10)]))
    story.append(cover)
    story.append(Spacer(1, 18 * mm))
    story.append(p('Use boundary: This document is not an approved refinery procedure, legal advice, emergency direction, or an operating authorization. It must be used with the site\'s controlled procedures and competent human decision-makers.', styles['callout']))
    story.append(PageBreak())

    skip_cover = True
    i = 0
    in_sources = False
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line == 'FICTIONAL DEMONSTRATION REFERENCE - NOT AN OPERATING AUTHORIZATION':
            continue
        if line.startswith('13. SOURCE REFERENCES'):
            in_sources = True
            story.append(p(line, styles['h1']))
            continue
        if in_sources:
            story.append(p(line, styles['small']))
            continue
        if re.match(r'^\d+\.\s', line):
            story.append(p(line, styles['h1']))
            continue
        if re.match(r'^\d+\.\d+\s', line):
            story.append(p(line, styles['h2']))
            continue
        if line.startswith('- '):
            story.append(p('- ' + line[2:], styles['bullet']))
            continue
        if line.startswith('T-') or line.startswith('Incident record:') or line.startswith('Executive finding:') or line.startswith('Evidence table:') or line.startswith('Applicable rules/protocols:') or line.startswith('Threshold assessment:') or line.startswith('Likely contributing conditions:') or line.startswith('Open evidence:') or line.startswith('Required next steps:') or line.startswith('Escalation decision:') or line.startswith('Deliverables:') or line.startswith('Human review boundary:'):
            story.append(p(line, styles['mono']))
            continue
        if line.startswith('IMPORTANT USE BOUNDARY') or line.startswith('REFERENCE BASIS') or line.startswith('Rule to cite'):
            story.append(p(line, styles['h2']))
            continue
        if line.startswith('END OF FICTIONAL'):
            story.append(Spacer(1, 8))
            story.append(p(line, styles['callout']))
            continue
        if line.startswith('SOP-RPS-001:') or line.startswith('Revision:') or line.startswith('Classification:'):
            story.append(p(line, styles['small']))
            continue
        story.append(p(line, styles['body']))
    doc.build(story)
    print(OUTPUT)


if __name__ == '__main__':
    build()
