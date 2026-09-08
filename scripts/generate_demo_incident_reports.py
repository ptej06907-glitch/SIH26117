from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

OUT = Path(__file__).resolve().parents[1] / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=22, leading=27, textColor=colors.HexColor('#17324d'), alignment=TA_CENTER, spaceAfter=12))
styles.add(ParagraphStyle(name='Section', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#17324d'), spaceBefore=10, spaceAfter=5))
styles.add(ParagraphStyle(name='BodySmall', parent=styles['BodyText'], fontSize=9.2, leading=13, textColor=colors.HexColor('#293b4d')))
styles.add(ParagraphStyle(name='Callout', parent=styles['BodyText'], fontSize=9, leading=13, textColor=colors.HexColor('#17324d'), backColor=colors.HexColor('#edf4f7'), borderColor=colors.HexColor('#c7d9e2'), borderWidth=.5, borderPadding=8, spaceBefore=5, spaceAfter=8))

REPORTS = [
    {
        'file':'incident_report_demo_crane_load.pdf','id':'INC-DEMO-2026-001','title':'Dropped Load Near Miss - Tank Farm Maintenance','date':'2026-09-03 10:35','asset':'Mobile maintenance crane MC-04, Tank Farm B','severity':'High potential near miss','reported':'R. Menon, Technician T-2041',
        'description':'During removal of a valve actuator, the suspended load rotated unexpectedly after a temporary tag line detached. The actuator descended approximately 0.6 m and landed inside the barricaded exclusion zone. No person was inside the zone and no injury occurred.',
        'immediate':'Stop work; lower and secure the load; isolate the crane; preserve the lifting arrangement; brief the crew; notify the area supervisor and safety representative.',
        'evidence':'Tag line knot was not secured with the specified secondary connection. The pre-lift briefing did not record a wind check. Barricade was present and remained intact.',
        'actions':'Reinspect the lift plan and rigging; quarantine the tag line; verify competent rigger assignment; repeat toolbox briefing; record supervisor release before restarting.',
    },
    {
        'file':'incident_report_demo_hydraulic_leak.pdf','id':'INC-DEMO-2026-002','title':'Hydraulic Oil Release and Slip Hazard','date':'2026-09-05 16:12','asset':'HP-800-03, Hydraulic Press Line 3','severity':'Recordable-potential incident','reported':'A. Khan, Operator T-1187',
        'description':'An operator observed hydraulic fluid spraying from the seal area during a controlled jog test after maintenance. Fluid reached the floor near the operator access path. No contact injury was reported, but the area became a slip and exposure hazard.',
        'immediate':'Stop the jog test; apply LOTO; restrict access; use the spill kit; report the release; inspect pressure readings and preserve the failed seal for examination.',
        'evidence':'Vibration at bearing B2 was recorded at 5.6 mm/s RMS. Accumulator pressure was 171 bar. Seal #4 showed an active leak. Maintenance log entries show worsening vibration and seal condition over three weeks.',
        'actions':'Keep the press isolated until the authorized maintenance supervisor confirms depressurization; replace the seal using the approved procedure; verify guards and housekeeping; perform a documented restart check.',
    },
    {
        'file':'incident_report_demo_confined_space.pdf','id':'INC-DEMO-2026-003','title':'Confined Space Permit Deviation','date':'2026-09-07 08:20','asset':'Vessel V-204, Utilities Area','severity':'Critical procedural deviation','reported':'S. Rao, Safety Observer S-031',
        'description':'A contractor team was preparing to enter a vessel while the entry permit displayed an expired gas-test timestamp. The entry supervisor identified the mismatch before entry and stopped the activity. No person entered the vessel under the expired reading.',
        'immediate':'Stop entry; withdraw the crew; suspend the permit; notify the permit issuer; repeat atmospheric testing with calibrated instruments; confirm isolation and rescue readiness.',
        'evidence':'Permit timestamp was outside the site-defined validity interval. The isolation certificate was present, but the attendant briefing record was incomplete. The rescue tripod was available at the access point.',
        'actions':'Reissue the permit only after a complete verification; conduct a focused contractor briefing; audit the permit handover process; require safety supervisor sign-off before any entry.',
    },
]

def footer(canvas, doc):
    canvas.saveState(); canvas.setStrokeColor(colors.HexColor('#d5e0e6')); canvas.line(18*mm, 15*mm, 192*mm, 15*mm)
    canvas.setFont('Helvetica', 7.5); canvas.setFillColor(colors.HexColor('#637789')); canvas.drawString(18*mm, 10*mm, 'FICTIONAL DEMONSTRATION DATA - Aegis local prototype')
    canvas.drawRightString(192*mm, 10*mm, f'Page {doc.page}'); canvas.restoreState()

def make(r):
    path=OUT/r['file']; doc=SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18*mm,leftMargin=18*mm,topMargin=17*mm,bottomMargin=22*mm)
    story=[Spacer(1,20*mm),Paragraph('INCIDENT REPORT', styles['CoverTitle']),Paragraph('Controlled demonstration record for local testing', styles['BodySmall']),Spacer(1,10*mm)]
    data=[[Paragraph('<b>Incident ID</b>',styles['BodySmall']),r['id']],[Paragraph('<b>Classification</b>',styles['BodySmall']),'Internal - Fictional demonstration'],[Paragraph('<b>Title</b>',styles['BodySmall']),r['title']],[Paragraph('<b>Date / time</b>',styles['BodySmall']),r['date']],[Paragraph('<b>Asset / location</b>',styles['BodySmall']),r['asset']],[Paragraph('<b>Severity</b>',styles['BodySmall']),r['severity']],[Paragraph('<b>Reported by</b>',styles['BodySmall']),r['reported']]]
    t=Table(data,colWidths=[42*mm,130*mm]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#e9f1f4')),('BOX',(0,0),(-1,-1),.6,colors.HexColor('#b8cbd5')),('INNERGRID',(0,0),(-1,-1),.3,colors.HexColor('#cfdae0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t);story.append(Spacer(1,12));story.append(Paragraph('This record is fictional and intended to test upload, OCR, evidence retrieval, incident analysis and supervisor review. It does not authorize work or establish a site procedure.',styles['Callout']))
    for heading,body in [('1. Event description',r['description']),('2. Immediate actions',r['immediate']),('3. Recorded evidence',r['evidence']),('4. Proposed follow-up',r['actions'])]: story.extend([Paragraph(heading,styles['Section']),Paragraph(body,styles['BodySmall'])])
    story.extend([Spacer(1,8),Paragraph('5. Review fields',styles['Section']),Paragraph('Supervisor disposition: ________________________________    Date: ________________',styles['BodySmall']),Spacer(1,7),Paragraph('Safety review required:  Yes / No       Work authorization required:  Yes / No',styles['BodySmall']),Spacer(1,7),Paragraph('Source documents attached:  Yes / No       Evidence verified:  Yes / No',styles['BodySmall'])])
    doc.build(story,onFirstPage=footer,onLaterPages=footer);return path

if __name__=='__main__':
    for report in REPORTS: print(make(report))
