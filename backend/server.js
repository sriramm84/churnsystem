// 🚀 FINAL BACKEND SERVER (FULLY FIXED + INTEGRATED)

const express = require("express");
const cors = require("cors");
const { MongoClient } = require("mongodb");
const { exec, spawn } = require("child_process");
const path = require("path");
const http = require("http");
const net = require("net");

const app = express();
app.use(cors());
app.use(express.json());

const MONGO_URI = "mongodb://127.0.0.1:27017";
const DB_NAME = "churn_system";
const COLLECTION = "scored_events";

let db;

/** 🔧 Run Windows commands safely */
function run(cmd) {
  return new Promise((resolve) => {
    exec(cmd, { windowsHide: true }, (err, stdout, stderr) => {
      if (err) return resolve({ ok: false, out: (stderr || err.message || "").trim() });
      resolve({ ok: true, out: (stdout || "").trim() });
    });
  });
}

/** 🔌 Check port status */
function checkPort(port) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(1000);

    socket.on("connect", () => {
      socket.destroy();
      resolve("UP");
    });

    socket.on("error", () => resolve("DOWN"));
    socket.on("timeout", () => resolve("DOWN"));

    socket.connect(port, "127.0.0.1");
  });
}

/** 🗄 MongoDB connection */
async function connectMongo() {
  const client = new MongoClient(MONGO_URI);
  await client.connect();
  db = client.db(DB_NAME);
  console.log("✅ MongoDB connected");
}

/** 🤖 ML SERVICE CONFIG */
const PREDICT_HOST = "http://127.0.0.1:5050";

/** 🔥 Call Flask ML service */
function callPredictionService(record) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(record);

    const req = http.request(
      `${PREDICT_HOST}/predict`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
        },
      },
      (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch {
            reject(new Error("Invalid JSON from ML service"));
          }
        });
      }
    );

    req.on("error", (e) =>
      reject(new Error(`ML service unreachable: ${e.message}`))
    );

    req.write(body);
    req.end();
  });
}

/** ✅ HEALTH CHECK */
app.get("/api/health", async (req, res) => {
  try {
    await db.command({ ping: 1 });
    res.json({ status: "ok", mongo: "connected" });
  } catch (e) {
    res.status(500).json({ status: "fail", error: String(e) });
  }
});

/** 📡 STREAM DATA */
app.get("/api/stream/latest", async (req, res) => {
  try {
    const docs = await db
      .collection(COLLECTION)
      .find({})
      .sort({ ingest_time: -1 })
      .limit(50)
      .toArray();

    res.json(docs);
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

/** 📊 STATS */
app.get("/api/stream/stats", async (req, res) => {
  try {
    const total = await db.collection(COLLECTION).countDocuments();

    const riskStats = await db
      .collection(COLLECTION)
      .aggregate([
        { $group: { _id: "$risk_level", count: { $sum: 1 } } },
        { $sort: { count: -1 } },
      ])
      .toArray();

    res.json({ total, riskStats });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

/** 🔍 SYSTEM MONITOR */
app.get("/api/monitor/status", async (req, res) => {
  try {
    const kafka = await checkPort(9092);
    const zk = await checkPort(2181);

    let mongoOk = true;
    try {
      await db.command({ ping: 1 });
    } catch {
      mongoOk = false;
    }

    res.json({
      kafka,
      zookeeper: zk,
      mongo: mongoOk ? "UP" : "DOWN",
      updated_at: new Date().toISOString(),
    });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

/** 🔥 MAIN PREDICTION ROUTE (UPDATED NAME) */
app.post("/predict-churn", async (req, res) => {
  try {
    const record = req.body;

    const result = await callPredictionService(record);

    res.json(result);
  } catch (e) {
    console.error("Prediction Error:", e.message);
    res.status(500).json({ error: e.message });
  }
});

/** 🚀 START SERVER */
const PORT = 5000;

connectMongo().then(() => {
  app.listen(PORT, "127.0.0.1", () => {
    console.log(`🚀 Backend running at http://127.0.0.1:${PORT}`);
  });
});