"""Trusted host wrapper. Guest Python receives no filesystem or network capabilities."""
import json,sys,threading
from pathlib import Path
import wasmtime
ROOT=Path(__file__).resolve().parent.parent

def execute(code):
    config=wasmtime.Config();config.consume_fuel=True;config.epoch_interruption=True
    engine=wasmtime.Engine(config)
    module=wasmtime.Module.from_file(engine,str(ROOT/'runtime/python.wasm'))
    store=wasmtime.Store(engine);store.set_limits(memory_size=256*1024*1024);store.set_fuel(2_000_000_000);store.set_epoch_deadline(1)
    wasi=wasmtime.WasiConfig();wasi.argv=['python','-B','-c',code]
    output=[];errors=[];counts=[0,0]
    def collect(target,index):
        def callback(data):
            remaining=max(0,16000-counts[index]);target.append(bytes(data[:remaining]).decode('utf-8',errors='replace'));counts[index]+=len(data);return len(data)
        return callback
    wasi.stdout_custom=collect(output,0);wasi.stderr_custom=collect(errors,1)
    # Deliberately no preopen_dir, inherit_env, inherit_stdin, sockets, or host imports.
    store.set_wasi(wasi);linker=wasmtime.Linker(engine);linker.define_wasi()
    timer=threading.Timer(10,engine.increment_epoch);timer.start();status=0;reason='completed'
    try:
        instance=linker.instantiate(store,module);instance.exports(store)['_start'](store)
    except wasmtime.ExitTrap as exc:status=exc.code
    except wasmtime.Trap as exc:status=1;reason=str(exc)[-500:]
    finally:timer.cancel()
    return {'exit_code':status,'stdout':''.join(output),'stderr':''.join(errors),'reason':reason,'truncated':any(c>16000 for c in counts),'isolation':'WebAssembly/WASI; no host directories, environment or network grants'}
if __name__=='__main__':
    request=json.load(sys.stdin)
    print(json.dumps(execute(request['code'])))
