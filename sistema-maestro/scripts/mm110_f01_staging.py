"""Restricted staging launcher; no institutional identity or production claim."""
import os
import re
from pathlib import Path
from mm110_f01_http import PilotServer
from mm110_f01_store import Store
from mm110_f01_postgres import PostgresStore

def configuration(env):
    origin=env.get("F01_STAGING_ORIGIN","")
    access=env.get("F01_STAGING_ACCESS","")
    backend=env.get("F01_STORAGE_BACKEND","sqlite")
    if backend not in ("sqlite","postgres"):
        raise ValueError("Unsupported persistence backend")
    if backend=="postgres":
        if not env.get("F01_DATABASE_URL"):
            raise ValueError("PostgreSQL connection required")
        if not origin or not access:
            raise ValueError("Explicit staging origin and review credential required")
        port=int(env.get("PORT","10000"))
        if not 1<=port<=65535:
            raise ValueError("Invalid service port")
        return port,None,origin,access
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

def deployment_commit(env):
    sha=env.get("RENDER_GIT_COMMIT")
    if sha is None and env.get("RENDER")!="true":
        return None
    if not isinstance(sha,str) or not re.fullmatch(r"[a-f0-9]{40}",sha):
        raise ValueError("Valid RENDER_GIT_COMMIT required")
    return sha

def build_store(env,path):
    if env.get("F01_STORAGE_BACKEND","sqlite")=="postgres":
        store=PostgresStore(env["F01_DATABASE_URL"])
        # Fail startup rather than reporting readiness with an unreachable database.
        store.token_count()
        return store
    return Store(path)

def main():
    port,path,origin,access=configuration(os.environ)
    sha=deployment_commit(os.environ)
    store=build_store(os.environ,path)
    with PilotServer(("0.0.0.0",port),store,
                     staging_origin=origin,staging_access=access,commit_sha=sha) as server:
        print("Restricted F01 staging ready",flush=True)
        server.serve_forever()

if __name__=="__main__":
    main()
