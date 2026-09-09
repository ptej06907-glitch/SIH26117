"""Run with the server stopped. Keeps a DPAPI-encrypted recovery copy."""
import sys
import sqlite3
import socket
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import vault

def migrate(root):
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(('127.0.0.1',8765))==0:raise RuntimeError('Stop the application on port 8765 before migration.')
    root=Path(root).resolve()
    path=root/'workbench.sqlite3'
    if not path.exists():raise RuntimeError('Database missing.')
    if path.read_bytes().startswith(vault.MAGIC):
        (root/'.encrypted-storage').touch()
        (root/'.require-antivirus').touch()
        return
    with sqlite3.connect(path) as con:
        if con.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0]:raise RuntimeError('Stop the application before migration.')
        con.execute('PRAGMA journal_mode=DELETE')
        original=con.serialize()
    con.close()
    backup=root/'workbench.pre-encryption.dpapi'
    if backup.exists():backup=root/('workbench.pre-encryption.'+uuid.uuid4().hex+'.dpapi')
    vault.write_bytes(backup,original,True)
    assert vault.read_bytes(backup)==original
    # Encrypt only data owned by the application. Do not traverse links.
    for folder in ('uploads','previews','artifacts'):
        for file in (root/folder).rglob('*'):
            if file.is_file() and file.resolve().is_relative_to(root) and not file.is_symlink():vault.seal(file)
    vault.write_bytes(path,original,True)
    (root/'.encrypted-storage').touch()
    with vault.database(path) as con:
        assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    (root/'.require-antivirus').touch()
    print('Database, uploads, previews and artifacts encrypted. Recovery copy verified.')

if __name__=='__main__':migrate(Path(__file__).resolve().parents[1]/'data')
