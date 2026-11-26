"""Restricted staging launcher; no institutional identity or production claim."""
import os
from pathlib import Path
from mm110_f01_http import PilotServer
from mm110_f01_store import Store

def configuration(env):
    origin=env.get("F01_STAGING_ORIGIN","")
    access=env.get("F01_STAGING_ACCESS","")
    mount=Path(env.get("F01_DATA_DIR",""))
    if not env.get("F01_DATA_DIR") or not mount.is_absolute() or not mount.is_dir():
        raise ValueError("Existing absolute durable data directory required")
    if env.get("RENDER")=="true" and not mount.is_mount():
        raise ValueError("Render persistent disk mount required")
    if not origin or not access:
        raise ValueError("Explicit staging origin and review credential required")
    port=int(env.get("PORT","10000"))
    if not 1<=port<=65535:
        raise ValueError("Invalid service port")
    return port,mount/"f01.sqlite",origin,access

def main():
    port,path,origin,access=configuration(os.environ)
    with PilotServer(("0.0.0.0",port),Store(path),
                     staging_origin=origin,staging_access=access) as server:
        print("Restricted F01 staging ready",flush=True)
        server.serve_forever()

if __name__=="__main__":
    main()
