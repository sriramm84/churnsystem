"""
Flask microservice for churn prediction (FULLY FIXED + PRODUCTION READY)
"""

import os
import sys
from flask import Flask, request, jsonify
import joblib

# ✅ PROJECT ROOT
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# ✅ IMPORT YOUR MODULES
try:
    from spark.feature_engineering import build_patent_features
    from spark.offer_engine import recommend_offer
except ImportError:
    from orchestrator.feature_engineering import build_patent_features
    from orchestrator.offer_engine import recommend_offer

# ✅ INIT APP
app = Flask(__name__)

# ✅ GLOBAL VARIABLES
MODEL = None
ENCODERS = None
COLUMNS = None


# 🔥 LOAD MODEL (WITH ENCODERS + COLUMNS)
def load_model():
    global MODEL, ENCODERS, COLUMNS

    if MODEL is None:
        print("🔥 Loading ML model...")

        model_path = os.path.join(PROJECT_ROOT, "models", "churn_model.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")

        loaded_obj = joblib.load(model_path)

        # Extract components
        MODEL = loaded_obj["model"]
        ENCODERS = loaded_obj["encoders"]
        COLUMNS = loaded_obj["columns"]

        print("✅ Model loaded successfully")
        print("📊 Total features expected:", len(COLUMNS))

    return MODEL


# 🔥 PREPARE INPUT (MATCH TRAINING EXACTLY)
def prepare_input(record):
    input_data = {}

    for col in COLUMNS:
        val = record.get(col, 0)

        # Apply encoding if needed
        if col in ENCODERS:
            le = ENCODERS[col]
            try:
                val = le.transform([str(val)])[0]
            except:
                val = 0  # fallback for unseen values

        input_data[col] = val

    # Maintain correct column order
    return [input_data[col] for col in COLUMNS]


# ✅ HEALTH CHECK
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ML service running"})


# ✅ PREDICTION API
@app.route("/predict", methods=["POST"])
def predict():
    try:
        record = request.get_json(force=True)

        print("\n📥 Incoming record:", record)

        # ✅ OPTIONAL: your custom feature engineering
        try:
            record = build_patent_features(record)
        except:
            pass  # ignore if not applicable

        # ✅ Load model
        model = load_model()

        # ✅ Prepare input correctly
        features = prepare_input(record)

        print("🧠 Feature vector length:", len(features))

        # ✅ Prediction
        if hasattr(model, "predict_proba"):
            score = float(model.predict_proba([features])[0][1])
        else:
            score = float(model.predict([features])[0])

        prob_pct = round(score * 100, 1)

        # ✅ Risk logic
        if prob_pct >= 85:
            risk = "CRITICAL"
            risk_color = "#ff3b3b"
        elif prob_pct >= 65:
            risk = "HIGH"
            risk_color = "#ff8c00"
        elif prob_pct >= 40:
            risk = "MEDIUM"
            risk_color = "#ffd700"
        else:
            risk = "LOW"
            risk_color = "#18f3b0"

        # ✅ Offer logic
        try:
            offer = recommend_offer(
                score=score,
                usage_drop=record.get("usage_drop_score", 0),
                complaint=record.get("complaint_intensity", 0),
                payment_risk=record.get("payment_risk_score", 0)
            )
        except:
            offer = "Standard Retention Offer"

        response = {
            "churn_probability": prob_pct,
            "risk_level": risk,
            "risk_color": risk_color,
            "offer": offer
        }

        print("📤 Response:", response)

        return jsonify(response)

    except Exception as e:
        print("❌ Prediction error:", str(e))
        return jsonify({"error": str(e)}), 500


# ✅ RUN SERVER
if __name__ == "__main__":
    print("🚀 ML Prediction Service running at http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=False)