"""Local connection observation and a Python-level outbound network guard."""
import socket,ipaddress,time,threading,os,json
from pathlib import Path
import psutil
from backend import vault
ATTEMPTS=[]
INSTALLED=False

def allowed(host):
    if isinstance(host,bytes):host=host.decode('ascii',errors='replace')
    if host=='localhost':return True
    try:return ipaddress.ip_address(host).is_loopback
    except ValueError:return False

def install_guard():
    global INSTALLED
    if INSTALLED:return
    original_connect=socket.socket.connect;original_connect_ex=socket.socket.connect_ex;original_sendto=socket.socket.sendto;original_getaddrinfo=socket.getaddrinfo
    def check(address):
        if isinstance(address,tuple) and not allowed(address[0]):
            ATTEMPTS.append({'time':int(time.time()),'host':str(address[0])[:100]});del ATTEMPTS[:-100]
            raise PermissionError('Aegis blocks non-loopback network destinations.')
    def connect(self,address):check(address);return original_connect(self,address)
    def connect_ex(self,address):check(address);return original_connect_ex(self,address)
    def sendto(self,*args):check(args[-1]);return original_sendto(self,*args)
    def getaddrinfo(host,*args,**kwargs):
        if host is not None:check((host,0))
        return original_getaddrinfo(host,*args,**kwargs)
    socket.socket.connect=connect;socket.socket.connect_ex=connect_ex;socket.socket.sendto=sendto;socket.getaddrinfo=getaddrinfo
    INSTALLED=True

class Monitor:
    def __init__(self,path):
        self.path=Path(path);self.stop_event=threading.Event();self.thread=None
        self.record={'started_at':int(time.time()),'samples':0,'external_connections':[],'observation_errors':0,'scope':'Python application and descendant processes; connection snapshots, not packet capture','packet_capture':'not_collected','python_guard':True}
    def start(self):
        install_guard();self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start()
    def loop(self):
        while not self.stop_event.is_set():
            try:
                processes=[psutil.Process(os.getpid())]+psutil.Process(os.getpid()).children(recursive=True)
                rows=[]
                for process in processes:
                    try:
                        for connection in process.net_connections(kind='inet'):
                            if connection.raddr:
                                row={'pid':process.pid,'peer':connection.raddr.ip,'port':connection.raddr.port,'status':connection.status}
                                rows.append(row)
                                if not allowed(connection.raddr.ip) and row not in self.record['external_connections']:self.record['external_connections'].append(row)
                    except (psutil.AccessDenied,psutil.NoSuchProcess):self.record['observation_errors']+=1
                self.record.update(samples=self.record['samples']+1,last_sample=int(time.time()),connections=rows,blocked_python_attempts=list(ATTEMPTS))
                self.path.parent.mkdir(parents=True,exist_ok=True)
                vault.write_bytes(self.path,json.dumps(self.record,indent=2).encode('utf-8'))
            except Exception:self.record['observation_errors']+=1
            self.stop_event.wait(.5)
    def close(self):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=2)
    def snapshot(self):return dict(self.record)
