OFFERS = [
    {"id": "O1", "name": "20% Discount", "cost": "high"},
    {"id": "O2", "name": "2GB Free Data Pack", "cost": "medium"},
    {"id": "O3", "name": "Priority Customer Support", "cost": "low"},
    {"id": "O4", "name": "3 Month OTT Subscription", "cost": "medium"},
    {"id": "O5", "name": "Flexible Payment Plan", "cost": "low"},
]

def recommend_offer(score: float, usage_drop: float, complaint: int, payment_risk: float):
    if score >= 0.85:
        if complaint >= 2:
            return OFFERS[2]
        if usage_drop >= 0.6:
            return OFFERS[1]
        if payment_risk >= 0.7:
            return OFFERS[4]
        return OFFERS[0]

    if 0.65 <= score < 0.85:
        if usage_drop >= 0.5:
            return OFFERS[1]
        return OFFERS[3]

    return {"id": "O0", "name": "Engagement SMS", "cost": "none"}
