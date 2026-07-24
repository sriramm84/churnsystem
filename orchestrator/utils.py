import os
import socket
import json
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

def wait_for_port(host: str, port: int, timeout_sec: int) -> bool:
    end = time.time() + timeout_sec
    while time.time() < end:
        if port_open(host, port):
            return True
        time.sleep(1)
    return False

def ensure_dir(p: str) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def write_audit(audit_path: str, record: dict) -> None:
    ensure_dir(os.path.dirname(audit_path))
    record = {"time": now_iso(), **record}
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=False)

def start_new_window(title: str, command: str, env: dict | None = None) -> subprocess.Popen:
    """
    Starts a new CMD window with a title:
    start "<TITLE>" cmd /k "<command>"
    Passes env vars explicitly so spawned process inherits them (critical for KAFKA_HEAP_OPTS).
    """
    full = f'start "{title}" cmd /k "{command}"'
    # Ensure the environment dict includes system variables if custom env is provided
    final_env = {**os.environ, **(env or {})} if env else None
    print(f"[{title}] Starting with env JAVA_HOME={final_env.get('JAVA_HOME', 'NOT SET') if final_env else 'inherited'}")
    return subprocess.Popen(full, shell=True, env=final_env)

def kill_windows_by_title(title_prefix: str) -> None:
    # Safe: only kills CMD windows (not Chrome)
    subprocess.run(
        [
            "taskkill",
            "/FI", "IMAGENAME eq cmd.exe",
            "/FI", f"WINDOWTITLE eq {title_prefix}*",
            "/T",
            "/F"
        ],
        capture_output=True,
        text=True
    )
