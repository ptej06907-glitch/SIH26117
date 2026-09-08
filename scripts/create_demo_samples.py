from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import pymupdf
root=Path('samples');root.mkdir(exist_ok=True)
lines=['FICTIONAL DEMONSTRATION REPORT','Inspection reference: DEMO-002','Equipment: P-101','Finding: identification label damaged.','Recommendation: replace the damaged label after review.','Cost: not provided.','No operational safety conclusion is supplied.']
image=Image.new('RGB',(1500,800),'white');draw=ImageDraw.Draw(image);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',32)
for i,line in enumerate(lines):draw.text((60,55+i*85),line,fill='black',font=font)
image.save(root/'inspection-scan.png')
pdf=pymupdf.open();page=pdf.new_page(width=750,height=400);page.insert_image(page.rect,filename=str(root/'inspection-scan.png'));pdf.save(root/'inspection-scan.pdf')
(root/'demo-sop.txt').write_text('FICTIONAL SOP DEMO-01 revision 1\nDamaged equipment identification labels require review by the maintenance supervisor. Costs must be supplied separately before financial approval. This is demonstration material, not an MRPL procedure.\n')
