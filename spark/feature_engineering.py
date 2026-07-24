import random

def build_patent_features(record: dict) -> dict:
    monthly = float(record.get("MonthlyCharges", 0))
    tenure = float(record.get("tenure", 0))

    # Novel engineered features (Patent style)
    record["usage_drop_score"] = round(random.uniform(0, 1), 3)
    record["complaint_intensity"] = random.randint(0, 3)

    if tenure <= 6 and monthly > 80:
        record["payment_risk_score"] = 1
    elif monthly > 70:
        record["payment_risk_score"] = 0.7
    else:
        record["payment_risk_score"] = 0.3

    return record
