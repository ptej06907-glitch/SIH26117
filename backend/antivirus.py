"""On-demand Windows Defender scan. Never change OS antivirus settings."""
from pathlib import Path
import subprocess

def defender_scan(path):
    root=Path('C:/ProgramData/Microsoft/Windows Defender/Platform')
    candidates=list(root.glob('*/MpCmdRun.exe'))
    if not candidates:raise RuntimeError('Windows Defender scan engine unavailable; upload rejected.')
    engine=max(candidates,key=lambda p:tuple(int(x) for x in p.parent.name.replace('-','.').split('.') if x.isdigit()))
    try:
        result=subprocess.run([str(engine),'-Scan','-ScanType','3','-File',str(Path(path).resolve()),'-DisableRemediation'],capture_output=True,timeout=60,creationflags=0x08000000)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise RuntimeError('Antivirus scan could not finish; upload rejected.') from exc
    if result.returncode!=0:raise RuntimeError('Antivirus found a threat or could not verify the file; upload rejected.')
    return {'engine':'Windows Defender','engine_version':engine.parent.name,'status':'passed'}
