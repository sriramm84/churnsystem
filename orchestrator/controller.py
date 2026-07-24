import os
import time
from collections import deque
from pathlib import Path

from config import Paths, Pipeline, Healing
from utils import (
    wait_for_port, port_open, run, start_new_window,
    write_audit, kill_windows_by_title, ensure_dir
)

paths = Paths()
pipe = Pipeline()
heal = Healing()

AUDIT_LOG = os.path.join(paths.PROJECT_HOME, "orchestrator", "audit", "recovery_log.jsonl")


def kafka_bin(*parts: str) -> str:
    return os.path.join(paths.KAFKA_HOME, "bin", "windows", *parts)

def spark_bin(*parts: str) -> str:
    return os.path.join(paths.SPARK_HOME, "bin", *parts)

def zk_props() -> str:
    return os.path.join(paths.KAFKA_HOME, "config", "zookeeper.properties")

def server_props() -> str:
    return os.path.join(paths.KAFKA_HOME, "config", "server.properties")

def checkpoint_dir() -> str:
    return os.path.join(paths.PROJECT_HOME, "spark", "checkpoints", "churn_stream")


def get_kafka_heap_env() -> dict:
    """Return dict of JVM heap env vars for Kafka/ZK — pass to start_new_window."""
    return {
        "KAFKA_HEAP_OPTS": "-Xms512m -Xmx1536m",
        "KAFKA_JVM_PERFORMANCE_OPTS": (
            "-XX:+UseG1GC "
            "-XX:MaxGCPauseMillis=20 "
            "-XX:InitiatingHeapOccupancyPercent=35 "
            "-XX:+ExplicitGCInvokesConcurrent "
            "-Djava.awt.headless=true"
        ),
        "KAFKA_LOG4J_OPTS": (
            f'-Dlog4j.configuration=file:"{paths.KAFKA_HOME}\\config\\log4j.properties"'
        ),
    }


def cleanup_stale_dirs() -> None:
    """Delete Kafka and ZK data directories before starting to ensure clean state."""
    import shutil
    dirs = [
        os.path.join(paths.KAFKA_HOME, "zookeeper-data"),
        os.path.join(paths.KAFKA_HOME, "zookeeper-logs"),
        os.path.join(paths.KAFKA_HOME, "kafka-logs"),
    ]
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
            print(f"[CLEANUP] Deleted {d}")


def cleanup_stale_zk_nodes() -> None:
    """
    Fix NodeExistsException: delete stale broker node.
    Uses piped commands so it WORKS on Windows.
    """
    print("[ZK_CLEANUP] Waiting 3s for ZooKeeper to be fully ready...")
    import time
    time.sleep(3)
    print("[ZK_CLEANUP] Now attempting to clean stale nodes...")
    cmd = (
        f'(echo deleteall /brokers/ids/0 & '
        f'echo deleteall /controller & '
        f'echo quit) | "{kafka_bin("zookeeper-shell.bat")}" {pipe.ZK_CONNECT}'
    )
    result = run(["cmd", "/c", cmd])
    if result.returncode == 0:
        print("[ZK_CLEANUP] [OK] Stale ZooKeeper nodes cleaned")
    else:
        print(f"[ZK_CLEANUP] WARNING: Cleanup returned code {result.returncode}, stderr: {result.stderr[:200]}")
    write_audit(AUDIT_LOG, {"action": "zk_cleanup", "detail": "deleteall /brokers/ids/0 and /controller", "rc": result.returncode})


def ensure_topic_exists() -> None:
    cp = run([
        kafka_bin("kafka-topics.bat"),
        "--bootstrap-server", pipe.BOOTSTRAP,
        "--create", "--if-not-exists",
        "--topic", pipe.TOPIC,
        "--partitions", "1",
        "--replication-factor", "1"
    ])
    write_audit(AUDIT_LOG, {"action": "topic_ensure", "rc": cp.returncode})


def clear_checkpoint_if_exists() -> None:
    ckp = checkpoint_dir()
    if os.path.exists(ckp):
        # delete checkpoint to avoid version mismatch / corrupted state issues
        import shutil
        shutil.rmtree(ckp, ignore_errors=True)
        write_audit(AUDIT_LOG, {"action": "checkpoint_deleted", "path": ckp})


def start_zookeeper() -> None:
    full_env = {**os.environ, **get_kafka_heap_env()}
    print("[ZOOKEEPER] Starting ZooKeeper...")
    proc = start_new_window(
        "ZOOKEEPER",
        f'"{kafka_bin("zookeeper-server-start.bat")}" "{zk_props()}"',
        env=full_env
    )
    print(f"[ZOOKEEPER] Waiting up to {heal.STARTUP_TIMEOUT_SEC}s for port {pipe.ZK_PORT}...")
    ok = wait_for_port("127.0.0.1", pipe.ZK_PORT, heal.STARTUP_TIMEOUT_SEC)
    if not ok:
        raise RuntimeError(f"ZooKeeper port {pipe.ZK_PORT} did not open after {heal.STARTUP_TIMEOUT_SEC}s. Check ZooKeeper window for errors.")
    write_audit(AUDIT_LOG, {"action": "zookeeper_started", "port": pipe.ZK_PORT})
    print("[ZOOKEEPER] [OK] ZooKeeper started successfully")


def start_kafka() -> None:
    full_env = {**os.environ, **get_kafka_heap_env()}
    print("[KAFKA] Starting Kafka broker...")
    start_new_window(
        "KAFKA",
        f'"{kafka_bin("kafka-server-start.bat")}" "{server_props()}"',
        env=full_env
    )
    print(f"[KAFKA] Waiting up to {heal.STARTUP_TIMEOUT_SEC}s for port {pipe.KAFKA_PORT}...")
    ok = wait_for_port("127.0.0.1", pipe.KAFKA_PORT, heal.STARTUP_TIMEOUT_SEC)
    if not ok:
        raise RuntimeError(f"Kafka port {pipe.KAFKA_PORT} did not open after {heal.STARTUP_TIMEOUT_SEC}s. Check Kafka window for errors.")
    write_audit(AUDIT_LOG, {"action": "kafka_started", "port": pipe.KAFKA_PORT})
    print("[KAFKA] [OK] Kafka started successfully")


def start_producer() -> None:
    start_new_window(
        "PRODUCER",
        f'"{paths.PYTHON_EXE}" "{pipe.PRODUCER_SCRIPT}"'
    )
    write_audit(AUDIT_LOG, {"action": "producer_started"})


def start_spark() -> None:
    # Spark python binding
    spark_env = {
        "PYSPARK_PYTHON": paths.PYTHON_EXE,
        "PYSPARK_DRIVER_PYTHON": paths.PYTHON_EXE,
    }

    clear_checkpoint_if_exists()

    cmd = (
        f'set PYSPARK_PYTHON={paths.PYTHON_EXE} && '
        f'set PYSPARK_DRIVER_PYTHON={paths.PYTHON_EXE} && '
        f'"{spark_bin("spark-submit.cmd")}" '
        f'--master local[*] '
        f'--packages {pipe.SPARK_PACKAGES} '
        f'--conf "spark.pyspark.python={paths.PYTHON_EXE}" '
        f'--conf "spark.pyspark.driver.python={paths.PYTHON_EXE}" '
        f'"{pipe.SPARK_SCRIPT}"'
    )
    print("[SPARK] Starting Spark Stream Consumer...")
    start_new_window("SPARK_STREAM", cmd, env=spark_env)
    print("[SPARK] [OK] Spark started (check SPARK_STREAM window for logs)")
    write_audit(AUDIT_LOG, {"action": "spark_started"})
    # Note: Spark health is monitored by checking if java processes exist
    # If Spark crashes, we'll see connection errors in the audit log


def stop_all() -> None:
    # close our CMD windows safely
    for t in ["PRODUCER", "SPARK_STREAM", "KAFKA", "ZOOKEEPER"]:
        kill_windows_by_title(t)

    # kill known executables safely
    run(["taskkill", "/F", "/IM", "spark-submit.cmd"])
    run(["taskkill", "/F", "/IM", "python.exe"])

    # kill Java processes by their window title (Kafka/ZK)
    for pattern in ["KAFKA*", "ZOOKEEPER*"]:
        run([
            "taskkill", "/F",
            "/FI", "IMAGENAME eq java.exe",
            "/FI", f"WINDOWTITLE eq {pattern}"
        ])

    # graceful stop scripts (best effort)
    run([kafka_bin("kafka-server-stop.bat")])
    run([kafka_bin("zookeeper-server-stop.bat")])

    write_audit(AUDIT_LOG, {"action": "stop_all"})


def healthy() -> dict:
    """
    Minimal health check signals.
    """
    return {
        "zookeeper_port": port_open("127.0.0.1", pipe.ZK_PORT),
        "kafka_port": port_open("127.0.0.1", pipe.KAFKA_PORT),
    }


def self_heal_loop() -> None:
    """
    Patent-worthy part: detect -> classify -> recover.
    """
    restart_timestamps = deque()  # timestamps of ACTUAL restarts only
    last_health_check = {}  # track last state to detect state CHANGES

    while True:
        h = healthy()
        
        # Detect actual failures (state change from UP to DOWN)
        fault_detected = False
        
        if not h["zookeeper_port"]:
            if last_health_check.get("zookeeper_port", True):  # was UP, now DOWN = fault
                write_audit(AUDIT_LOG, {"event": "fault", "type": "ZK_DOWN"})
                fault_detected = True
                stop_all()
                cleanup_stale_dirs()
                start_zookeeper()
                cleanup_stale_zk_nodes()
                start_kafka()
                ensure_topic_exists()
                start_producer()
                start_spark()

        elif not h["kafka_port"]:
            if last_health_check.get("kafka_port", True):  # was UP, now DOWN = fault
                write_audit(AUDIT_LOG, {"event": "fault", "type": "KAFKA_DOWN"})
                fault_detected = True
                cleanup_stale_dirs()
                kill_windows_by_title("KAFKA")
                cleanup_stale_zk_nodes()
                start_kafka()
                ensure_topic_exists()

        # ONLY increment on ACTUAL restarts, not on every loop
        if fault_detected:
            now = time.time()
            restart_timestamps.append(now)
            
            # Keep only restarts from last hour
            while restart_timestamps and now - restart_timestamps[0] > 3600:
                restart_timestamps.popleft()
            
            # Safety limit: stop if too many restarts in one hour
            if len(restart_timestamps) > heal.MAX_RESTARTS_PER_HOUR:
                write_audit(AUDIT_LOG, {"event": "safety_stop", "reason": "too_many_restarts", "count": len(restart_timestamps)})
                print(f"[SAFETY] Too many restarts ({len(restart_timestamps)}) in past hour. Stopping.")
                break
        
        # Save current health state for next iteration
        last_health_check = h.copy()
        time.sleep(heal.CHECK_INTERVAL_SEC)


def bootstrap_once() -> None:
    # start with a clean audit dir
    ensure_dir(os.path.dirname(AUDIT_LOG))
    write_audit(AUDIT_LOG, {"event": "bootstrap_start"})

    # CRITICAL: delete stale Kafka/ZK data dirs before starting anything
    cleanup_stale_dirs()

    start_zookeeper()
    cleanup_stale_zk_nodes()

    start_kafka()
    ensure_topic_exists()

    start_producer()
    print("Spark packages:", pipe.SPARK_PACKAGES)
    start_spark()


    write_audit(AUDIT_LOG, {"event": "bootstrap_done"})


def main():
    bootstrap_once()
    self_heal_loop()


if __name__ == "__main__":
    main()
