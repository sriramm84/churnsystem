import pandas as pd
import joblib

MODEL_PATH = "models/churn_model.pkl"

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
encoders = bundle["encoders"]
columns = bundle["columns"]

def preprocess_one(record: dict):
    df = pd.DataFrame([record])

    if "customerID" in df.columns:
        df.drop(columns=["customerID"], inplace=True)

    if "TotalCharges" in df.columns:
        df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)

    for col, le in encoders.items():
        if col in df.columns:
            df[col] = df[col].astype(str).apply(lambda x: x if x in le.classes_ else le.classes_[0])
            df[col] = le.transform(df[col].astype(str))

    for c in columns:
        if c not in df.columns:
            df[c] = 0

    return df[columns]

def churn_score(record: dict) -> float:
    X = preprocess_one(record)
    prob = model.predict_proba(X)[0][1]
    return float(prob)
