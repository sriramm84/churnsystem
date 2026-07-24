from dataclasses import dataclass

@dataclass
class Paths:
    KAFKA_HOME: str = r"D:\kafka_2.13-3.7.0"
    SPARK_HOME: str = r"D:\spark-4.1.1-bin-hadoop3"
    PROJECT_HOME: str = r"D:\sem-6\ChurnSystem"
    PYTHON_EXE: str = r"C:\Python313\python.exe"

@dataclass
class Pipeline:
    ZK_PORT: int = 2181
    KAFKA_PORT: int = 9092
    BOOTSTRAP: str = "127.0.0.1:9092"
    ZK_CONNECT: str = "127.0.0.1:2181"
    TOPIC: str = "churn-topic"

    PRODUCER_SCRIPT: str = r"D:\sem-6\ChurnSystem\kafka\producer.py"
    SPARK_SCRIPT: str = r"D:\sem-6\ChurnSystem\spark\stream_consumer.py"

    # Spark Kafka connector MUST match Spark version 4.1.1
    SPARK_PACKAGES: str = (
    "org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1,"
    "org.apache.spark:spark-token-provider-kafka-0-10_2.13:4.1.1,"
    "org.mongodb.spark:mongo-spark-connector_2.13:10.4.0"
)


@dataclass
class Healing:
    CHECK_INTERVAL_SEC: int = 5
    STARTUP_TIMEOUT_SEC: int = 240  # Increased from 120 to allow Kafka/ZK proper startup time
    MAX_RESTARTS_PER_HOUR: int = 25  # safety
