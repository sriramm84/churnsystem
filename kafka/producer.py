import json
import random
import time
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

SERVER = "127.0.0.1:9092"
TOPIC = "churn-topic"


def get_producer(retries=30, sleep_sec=2):
    for i in range(retries):
        try:
            print(f"Connecting to Kafka... attempt {i+1}/{retries}")
            producer = KafkaProducer(
                bootstrap_servers=SERVER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=10,
                request_timeout_ms=20000,
                api_version_auto_timeout_ms=15000,
                linger_ms=50
            )
            print("Kafka producer connected.")
            return producer
        except NoBrokersAvailable:
            print("Kafka not ready yet. Retrying...")
            time.sleep(sleep_sec)

    raise RuntimeError("Kafka broker not available even after retries.")


def generate_record():
    """
    Generate a random churn-like record.
    Change this schema if your model requires other columns.
    """
    customer_id = f"C{random.randint(100, 999)}"
    age = random.randint(18, 65)
    tenure = random.randint(1, 60)
    monthly_charges = round(random.uniform(20.0, 120.0), 2)
    contract = random.choice(["Month-to-month", "One year", "Two year"])

    return {
        "customer_id": customer_id,
        "age": age,
        "tenure": tenure,
        "monthly_charges": monthly_charges,
        "contract": contract,
        "event_time": datetime.now().isoformat()
    }


def main():
    producer = get_producer()
    print(f"Producing messages to topic: {TOPIC}")
    print("Press CTRL + C to stop.\n")

    try:
        while True:
            record = generate_record()

            # send record
            producer.send(TOPIC, value=record)
            producer.flush()

            print("Sent:", record)
            time.sleep(2)  # send every 2 seconds
    except KeyboardInterrupt:
        print("\nStopping producer...")
    finally:
        try:
            producer.close()
        except:
            pass


if __name__ == "__main__":
    main()
