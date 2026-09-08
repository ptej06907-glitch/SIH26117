"""Bounded local extraction and deterministic evidence selection."""
from pathlib import Path
import re, threading, io
import pymupdf
from PIL import Image

OCR_LOCK=threading.Lock()
OCR=None
Image.MAX_IMAGE_PIXELS=25_000_000

def ocr_image(image):
    global OCR
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR
    with OCR_LOCK:
        if OCR is None:OCR=RapidOCR()
        image=image.convert('RGB');image.thumbnail((1800,1800))
        result,_=OCR(np.array(image))
    rows=result or []
    return '\n'.join(row[1] for row in rows), [{'text':row[1],'confidence':round(float(row[2]),3),'box':row[0]} for row in rows]

def extract(path,filename,preview_dir,document_id):
    suffix=Path(filename).suffix.lower();preview_dir=Path(preview_dir);preview_dir.mkdir(parents=True,exist_ok=True)
    pages=[]
    if suffix in {'.txt','.csv'}:
        text=Path(path).read_text(encoding='utf-8-sig')
        if len(text)>120000:raise ValueError('Text extraction is limited to 120,000 characters per file.')
        pages=[{'page':1,'text':text,'method':'text','warnings':[],'lines':[]}]
    elif suffix=='.pdf':
        with pymupdf.open(path) as pdf:
            if pdf.needs_pass:raise ValueError('Password-protected PDFs are not supported.')
            if len(pdf)>20:raise ValueError('Use a PDF with 20 pages or fewer for this prototype.')
            for index,page in enumerate(pdf):
                text=page.get_text()[:12000]
                scale=min(2.0,1800/max(page.rect.width,page.rect.height))
                pix=page.get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False)
                image=Image.open(io.BytesIO(pix.tobytes('png')))
                image.save(preview_dir/f'{document_id}-{index+1}.png')
                lines=[];method='pdf_text'
                if len(text.strip())<30:text,lines=ocr_image(image);method='ocr'
                warnings=[]
                if not text.strip():warnings.append('No readable text found. Review the page image.')
                if method=='ocr':warnings.append('OCR may misread measurements, identifiers and handwriting. Check the original page.')
                pages.append({'page':index+1,'text':text[:12000],'method':method,'warnings':warnings,'lines':lines})
    else:
        with Image.open(path) as image:
            image.load();image.thumbnail((1800,1800));image.convert('RGB').save(preview_dir/f'{document_id}-1.png')
            text,lines=ocr_image(image)
        pages=[{'page':1,'text':text[:12000],'method':'ocr','warnings':['OCR text requires review; empty text does not mean an empty image.'],'lines':lines}]
    return pages

STOP={'the','a','an','is','are','of','to','and','in','for','this','that','what','please','write','draft','note','report','using','from','with','summarize','inspection'}
def tokens(text):return set(re.findall(r'[a-z0-9][a-z0-9_-]{1,}',text.lower()))-STOP

def retrieve(records,query,limit=3):
    wanted=tokens(query);scored=[]
    for record in records:
        text=record['text']
        for start in range(0,len(text),600):
            chunk=text[start:start+800].strip()
            if not chunk:continue
            score=len(tokens(chunk)&wanted)
            if score:scored.append((score,record,chunk))
    scored.sort(key=lambda x:x[0],reverse=True)
    evidence=[]
    for _,record,chunk in scored[:limit]:
        evidence.append({'ref':f'S{len(evidence)+1}','document_id':record['document_id'],'filename':record['filename'],'page':record['page'],'text':chunk[:600]})
    return evidence

def context_for(evidence):
    return '\n\n'.join(f"[{e['ref']}] {e['filename']} page {e['page']}\n{e['text']}" for e in evidence)
