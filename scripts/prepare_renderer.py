from pathlib import Path
import urllib.request
p=Path('runtime/libreoffice.msi')
if not p.exists():
 with urllib.request.urlopen('https://download.documentfoundation.org/libreoffice/stable/26.2.6/win/x86_64/LibreOffice_26.2.6_Win_x86-64.msi',timeout=120) as r,p.with_suffix('.part').open('wb') as f:
  while block:=r.read(1024*1024):f.write(block)
 p.with_suffix('.part').replace(p)
print('Office renderer downloaded')
