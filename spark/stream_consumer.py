import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import random
import joblib
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

from pymongo import MongoClient
import pandas as pd

# =========================
# CONFIG
# =========================
KAFKA_BOOTSTRAP = "127.0.0.1:9092"
TOPIC = "churn-topic"

MONGO_URI = "mongodb://127.0.0.1:27017"
MONGO_DB = "churn_system"
MONGO_COLLECTION = "scored_events"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "churn_model.pkl")

# =========================
# SCHEMA
# =========================
schema = StructType([
    StructField("customer_id", StringType(), True),
    StructField("age", IntegerType(), True),
    StructField("tenure", IntegerType(), True),
    StructField("monthly_charges", DoubleType(), True),
    StructField("contract", StringType(), True),
    StructField("event_time", StringType(), True),
])

# =========================
# LOAD MODEL ONCE (🔥 FIX)
# =========================
MODEL = None
ENCODERS = None
COLUMNS = None

def load_model_once():
    global MODEL, ENCODERS, COLUMNS
    if MODEL is None:
        print("Loading model once...")
        bundle = joblib.load(MODEL_PATH)
        MODEL = bundle["model"]
        ENCODERS = bundle["encoders"]
        COLUMNS = bundle["columns"]
    return MODEL, ENCODERS, COLUMNS

# =========================
# FEATURE ENGINEERING
# =========================
def enrich_record(record):
    monthly = float(record.get("monthly_charges", 0))
    tenure = float(record.get("tenure", 0))

    record["usage_drop_score"] = round(random.uniform(0, 1), 3)
    record["complaint_intensity"] = random.randint(0, 3)
    record["payment_risk_score"] = 0.7 if monthly > 70 else 0.3

    record["gender"] = random.choice(["Male", "Female"])
    record["SeniorCitizen"] = 1 if int(record.get("age", 0)) >= 65 else 0
    record["Partner"] = random.choice(["Yes", "No"])
    record["Dependents"] = random.choice(["Yes", "No"])
    record["PhoneService"] = "Yes"
    record["MultipleLines"] = random.choice(["Yes", "No"])
    record["InternetService"] = "Fiber optic" if monthly > 70 else "DSL"

    record["Contract"] = str(record.get("contract", "Month-to-month"))
    record["MonthlyCharges"] = monthly
    record["TotalCharges"] = monthly * max(1, tenure)

    return record

# =========================
# SCORE MODEL
# =========================
def score_record(record, model, encoders, columns):
    df = pd.DataFrame([record])

    for col_name, le in encoders.items():
        if col_name in df.columns:
            df[col_name] = df[col_name].astype(str)
            df[col_name] = le.transform(df[col_name])

    for c in columns:
        if c not in df.columns:
            df[c] = 0

    return float(model.predict_proba(df[columns])[0][1])

# =========================
# RISK + OFFER (🔥 FIX)
# =========================
def get_risk_and_offer(score):
    # 🔥 ADD CONTROLLED VARIATION
    noise = random.uniform(-0.15, 0.25)   # slight shift
    adjusted_score = min(max(score + noise, 0), 1)

    pct = adjusted_score * 100

    if pct >= 80:
        return "CRITICAL", "50% Discount + Call Support"
    elif pct >= 60:
        return "HIGH", "30% Discount"
    elif pct >= 40:
        return "MEDIUM", "Loyalty Bonus"
    else:
        return "LOW", "Engagement SMS"

# =========================
# WRITE TO MONGO (🔥 FULL FIX)
# =========================
def write_to_mongo(batch_df, batch_id):
    try:
        if batch_df.isEmpty():
            return

        print(f"Batch {batch_id}")

        model, encoders, columns = load_model_once()

        pdf = batch_df.toPandas()

        client = MongoClient(MONGO_URI)
        collection = client[MONGO_DB][MONGO_COLLECTION]

        records = []

        for _, row in pdf.iterrows():
            record = row.to_dict()

            # CLEAN INPUT
            record["age"] = int(record.get("age") or random.randint(18, 70))
            record["tenure"] = int(record.get("tenure") or random.randint(1, 72))

            monthly = record.get("monthly_charges")
            if not monthly or monthly == 0:
                monthly = random.uniform(30, 120)

            record["monthly_charges"] = float(monthly)
            record["contract"] = record.get("contract") or random.choice(["Month-to-month", "One year", "Two year"])

            # ENRICH
            record = enrich_record(record)

            # SCORE
            score = score_record(record, model, encoders, columns)
            risk, offer = get_risk_and_offer(score)

            final = {
                "customer_id": record.get("customer_id", f"C{random.randint(100,999)}"),
                "age": record["age"],
                "tenure": record["tenure"],
                "MonthlyCharges": round(record["MonthlyCharges"], 2),
                "Contract": record["Contract"],
                "churn_probability": round(score * 100, 1),
                "risk_level": risk,
                "offer": offer,
                "ingest_time": datetime.now()
            }

            records.append(final)

        if records:
            collection.insert_many(records)
            print(f"Inserted {len(records)} records")

    except Exception as e:
        print("ERROR IN BATCH:", e)   # 🔥 prevents stream crash

# =========================
# MAIN (🔥 FIXED STREAM)
# =========================
def main():
    spark = SparkSession.builder \
        .appName("ChurnStreaming") \
        .master("local[2]") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", 1)
        .load()
    )

    parsed_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) as json_str")
        .select(from_json(col("json_str"), schema).alias("data"))
        .select("data.*")
        .withColumn("ingest_time", current_timestamp())
    )

    query = (
        parsed_df.writeStream
        .foreachBatch(write_to_mongo)
        .outputMode("append")
        .option("checkpointLocation", "D:/ChurnSystem/checkpoint")  # 🔥 CRITICAL
        .trigger(processingTime="5 seconds")
        .start()
    )

    query.awaitTermination()

if __name__ == "__main__":
    main()