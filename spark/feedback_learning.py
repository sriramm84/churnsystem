import json
import os
from datetime import datetime
import random

FEEDBACK_FILE = "data/feedback.jsonl"

def store_feedback(customer_key: str, score: float, offer: dict, accepted: bool):
    os.makedirs("data", exist_ok=True)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "customer_key": customer_key,
        "churn_score": round(score, 4),
        "offer_id": offer["id"],
        "offer_name": offer["name"],
        "accepted": accepted
    }

    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def simulate_acceptance(score: float) -> bool:
    if score >= 0.85:
        return random.random() > 0.55
    elif score >= 0.65:
        return random.random() > 0.35
    else:
        return random.random() > 0.20
