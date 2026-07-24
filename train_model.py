import pandas as pd
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

DATA_PATH = "data/Telco-Customer-Churn.csv"
MODEL_PATH = "models/churn_model.pkl"

def preprocess(df: pd.DataFrame):
    df = df.copy()

    if "customerID" in df.columns:
        df.drop(columns=["customerID"], inplace=True)

    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(df["TotalCharges"].median())

    df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})

    encoders = {}
    for c in df.columns:
        if df[c].dtype == "object":
            le = LabelEncoder()
            df[c] = le.fit_transform(df[c].astype(str))
            encoders[c] = le

    X = df.drop("Churn", axis=1)
    y = df["Churn"]
    return X, y, encoders

def main():
    df = pd.read_csv(DATA_PATH)
    X, y, encoders = preprocess(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=12,
        random_state=42,
        class_weight="balanced"
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n✅ Model Evaluation:\n")
    print(classification_report(y_test, y_pred))

    os.makedirs("models", exist_ok=True)
    joblib.dump(
        {"model": model, "encoders": encoders, "columns": X.columns.tolist()},
        MODEL_PATH
    )
    print(f"\n✅ Model saved at: {MODEL_PATH}")

if __name__ == "__main__":
    main()
