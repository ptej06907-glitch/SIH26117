"""Windows-user-bound DPAPI storage for this single-process workstation."""
import ctypes
from ctypes import wintypes
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
import sqlite3
import os
import msvcrt

MAGIC=b'AEGIS-DPAPI-1\x00'
LOCK=RLock()

class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]

def transform(data, decrypt=False):
    if os.name!='nt':raise RuntimeError('This vault requires Windows DPAPI.')
    buffer=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)))
    target=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.LocalFree.argtypes=[ctypes.c_void_p]
    kernel.LocalFree.restype=ctypes.c_void_p
    if decrypt:
        ok=crypt.CryptUnprotectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target))
    else:
        ok=crypt.CryptProtectData(ctypes.byref(source),'Aegis local data',None,None,None,1,ctypes.byref(target))
    if not ok:raise ctypes.WinError(ctypes.get_last_error())
    try:return ctypes.string_at(target.data,target.size)
    finally:kernel.LocalFree(target.data)

def enabled(path):
    return any((parent/'.encrypted-storage').exists() for parent in Path(path).resolve().parents)

def read_bytes(path):
    data=Path(path).read_bytes()
    return transform(data[len(MAGIC):],True) if data.startswith(MAGIC) else data

def write_bytes(path,data,force=False):
    path=Path(path)
    blob=MAGIC+transform(data) if force or enabled(path) else data
    temp=path.with_name(path.name+'.sealed-part')
    temp.write_bytes(blob)
    os.replace(temp,path)

def seal(path):
    path=Path(path)
    data=path.read_bytes()
    if not data.startswith(MAGIC):write_bytes(path,data,True)

@contextmanager
def database(path):
    with LOCK:
        lockfile=open(str(path)+'.lock','a+b')
        lockfile.seek(0)
        try:msvcrt.locking(lockfile.fileno(),msvcrt.LK_LOCK,1)
        except BaseException:lockfile.close();raise
        con=sqlite3.connect(':memory:')
        try:
            if Path(path).exists():con.deserialize(read_bytes(path))
            con.row_factory=sqlite3.Row
            con.execute('PRAGMA foreign_keys=ON')
            schema=con.execute('PRAGMA schema_version').fetchone()[0]
            with con:yield con
            if con.total_changes or con.execute('PRAGMA schema_version').fetchone()[0]!=schema:
                write_bytes(path,con.serialize(),True)
        finally:
            con.close();lockfile.seek(0);msvcrt.locking(lockfile.fileno(),msvcrt.LK_UNLCK,1);lockfile.close()
