import React, { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:5000/api";

// -------------------------
// Live Monitoring Component
// -------------------------
function StatusCard({ name, value, goodIf = ["UP", "OK", "CONNECTED"] }) {
  const v = String(value ?? "");
  const ok = goodIf.some((x) => v.toUpperCase().includes(x));
  return (
    <div className="status-card">
      <div className="status-label">{name}</div>
      <div className={`status-value ${ok ? "good" : "bad"}`}>{v}</div>
    </div>
  );
}

function MonitorPanel() {
  const [status, setStatus] = useState(null);
  const [err, setErr] = useState("");

  async function loadStatus() {
    try {
      setErr("");
      const data = await fetch("http://127.0.0.1:5000/api/monitor/status")
        .then((r) => r.json());
      setStatus(data);
    } catch (e) {
      setErr("Monitoring API not reachable");
    }
  }

  useEffect(() => {
    loadStatus(); // initial load

    const interval = setInterval(() => {
      loadStatus(); // refresh every 3 sec
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="glass-panel">
      <div className="panel-title">System Status</div>
      <div className="panel-sub">Updates every 3 seconds</div>

      {err && <div className="neb-alert"><b>Error:</b> {err}</div>}

      {!status ? (
        <div className="loading">Loading…</div>
      ) : (
        <div className="status-grid">
          <StatusCard name="Kafka Broker (9092)" value={status.kafka} goodIf={["UP"]} />
          <StatusCard name="Zookeeper (2181)" value={status.zookeeper} goodIf={["UP"]} />
          <StatusCard name="MongoDB" value={status.mongo} goodIf={["UP"]} />
          <StatusCard name="Java process count" value={status.java_process_count} goodIf={["1","2","3","4","5","6","7","8","9"]} />
          <StatusCard name="Updated at" value={status.updated_at} goodIf={["202"]} />
        </div>
      )}
    </div>
  );
}

// -------------------------
// Churn Prediction Component
// -------------------------
function PredictionPanel() {
  const [form, setForm] = useState({
    customer_id: "",
    age: "",
    tenure: "",
    monthly_charges: "",
    contract: "Month-to-month",
    usage_drop_score: "0.5",
    complaint_intensity: "1",
    payment_risk_score: "0.5",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const payload = {
  ...form,
  age: parseInt(form.age) || 0,
  tenure: parseInt(form.tenure) || 0,
  MonthlyCharges: parseFloat(form.monthly_charges) || 0,
  Contract: form.contract,
  usage_drop_score: parseFloat(form.usage_drop_score) || 0,
  complaint_intensity: parseInt(form.complaint_intensity) || 0,
  payment_risk_score: parseFloat(form.payment_risk_score) || 0,
};
      const res = await fetch("http://127.0.0.1:5000/predict-churn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError("Prediction service unavailable. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const prob = result ? result.churn_probability : 0;
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (prob / 100) * circumference;

  return (
    <div className="glass-panel pred-panel">
      <div className="panel-title">Churn Prediction Engine</div>
      <div className="panel-sub">Enter customer attributes to predict churn risk & offer</div>

      <form className="pred-form" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label className="form-group">
            <span>Customer ID</span>
            <input name="customer_id" value={form.customer_id} onChange={handleChange} placeholder="e.g. 7590-VHVEG" required />
          </label>
          <label className="form-group">
            <span>Age</span>
            <input name="age" type="number" value={form.age} onChange={handleChange} placeholder="e.g. 35" required />
          </label>
          <label className="form-group">
            <span>Tenure (months)</span>
            <input name="tenure" type="number" value={form.tenure} onChange={handleChange} placeholder="e.g. 12" required />
          </label>
          <label className="form-group">
            <span>Monthly Charges ($)</span>
            <input name="monthly_charges" type="number" step="0.01" value={form.monthly_charges} onChange={handleChange} placeholder="e.g. 70.50" required />
          </label>
          <label className="form-group">
            <span>Contract</span>
            <select name="contract" value={form.contract} onChange={handleChange}>
              <option>Month-to-month</option>
              <option>One year</option>
              <option>Two year</option>
            </select>
          </label>
          <label className="form-group">
            <span>Usage Drop Score (0–1)</span>
            <input name="usage_drop_score" type="number" step="0.01" min="0" max="1" value={form.usage_drop_score} onChange={handleChange} />
          </label>
          <label className="form-group">
            <span>Complaint Intensity (0–3)</span>
            <input name="complaint_intensity" type="number" min="0" max="3" value={form.complaint_intensity} onChange={handleChange} />
          </label>
          <label className="form-group">
            <span>Payment Risk Score (0–1)</span>
            <input name="payment_risk_score" type="number" step="0.01" min="0" max="1" value={form.payment_risk_score} onChange={handleChange} />
          </label>
        </div>

        <button type="submit" className="pred-btn" disabled={loading}>
          {loading ? (
            <span className="pred-btn-loading">
              <span className="spinner" /> Analyzing…
            </span>
          ) : (
            "⚡ Predict Churn"
          )}
        </button>

        {error && <div className="neb-alert">{error}</div>}
      </form>

      {/* Result */}
      {result && (
        <div className="pred-result">
          {/* Score circle */}
          <div className="score-ring-wrap">
            <svg className="score-ring" viewBox="0 0 120 120">
              <circle className="ring-bg" cx="60" cy="60" r="54" />
              <circle
                className="ring-fill"
                cx="60" cy="60" r="54"
                style={{
                  stroke: result.risk_color,
                  strokeDasharray: circumference,
                  strokeDashoffset: offset,
                }}
              />
            </svg>
            <div className="score-center">
              <div className="score-pct" style={{ color: result.risk_color }}>
                {prob}%
              </div>
              <div className="score-label">churn prob</div>
            </div>
          </div>

          {/* Risk badge */}
          <div className="risk-badge" style={{ borderColor: result.risk_color, color: result.risk_color }}>
            🔴 {result.risk_level} RISK
          </div>

          {/* Features */}
          <div className="feat-grid">
            <div className="feat-item">
              <span className="feat-name">Usage Drop</span>
              <div className="feat-bar">
                <div className="feat-fill" style={{
                  width: `${(result.features.usage_drop_score || 0) * 100}%`,
                  background: result.risk_color
                }} />
              </div>
              <span className="feat-val">{(result.features.usage_drop_score || 0).toFixed(3)}</span>
            </div>
            <div className="feat-item">
              <span className="feat-name">Complaint</span>
              <div className="feat-bar">
                <div className="feat-fill" style={{
                  width: `${(result.features.complaint_intensity || 0) / 3 * 100}%`,
                  background: result.risk_color
                }} />
              </div>
              <span className="feat-val">{result.features.complaint_intensity || 0}</span>
            </div>
            <div className="feat-item">
              <span className="feat-name">Payment Risk</span>
              <div className="feat-bar">
                <div className="feat-fill" style={{
                  width: `${(result.features.payment_risk_score || 0) * 100}%`,
                  background: result.risk_color
                }} />
              </div>
              <span className="feat-val">{(result.features.payment_risk_score || 0).toFixed(3)}</span>
            </div>
          </div>

          {/* Offer */}
          <div className="offer-card">
            <div className="offer-title">🎯 Recommended Offer</div>
            <div className="offer-name">{result.offer?.name || "Engagement SMS"}</div>
            <div className="offer-cost">Cost tier: <b>{result.offer?.cost || "none"}</b></div>
          </div>
        </div>
      )}
    </div>
  );
}

// -------------------------
// Main App
// -------------------------
export default function App() {
  const [rows, setRows] = useState([]);
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  async function safeFetch(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function loadAll() {
    try {
      setError("");
      const [h, s, latest] = await Promise.all([
        safeFetch(`${API}/health`),
        safeFetch(`${API}/stream/stats`),
        safeFetch(`${API}/stream/latest`),
      ]);
      setHealth(h);
      setStats(s);
      setRows([...latest]); // force React refresh
    } catch (e) {
      setError("Backend API not reachable. Start backend: cd backend && npm start");
    }
  }

  useEffect(() => {
    loadAll();
    const t = setInterval(loadAll, 3000);
    return () => clearInterval(t);
  }, []);

  const filteredRows = rows.filter((r) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      String(r.customer_id || "").toLowerCase().includes(q) ||
      String(r.Contract || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="neb-root">
      {/* NAVBAR */}
      <header className="neb-nav">
        <div className="neb-brand">
          <div className="bolt">⚡</div>
          <div className="brand-text">
            <div className="brand-name">CHURNAX</div>
            <div className="brand-sub">Self-Healing Streaming Platform</div>
          </div>
        </div>

        <nav className="neb-links">
          <a href="#home" className="active">Home</a>
          <a href="#pipeline">Pipeline</a>
          <a href="#analytics">Analytics</a>
          <a href="#logs">Recovery</a>
        </nav>

        {/* ✅ Live Monitoring button now works */}
        <button
          className="neb-btn"
          onClick={() => {
            const el = document.getElementById("pipeline");
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
        >
          Live Monitoring
        </button>
      </header>

      {/* CHURN PREDICTION */}
      <section className="neb-section" id="predict">
        <div className="section-head">
          <h2>Churn Prediction</h2>
        </div>
        <PredictionPanel />
      </section>

      {/* HERO */}
      <section className="neb-hero" id="home">
        <div className="hero-left">
          <div className="hero-badge">
            <span className="dot" />
            Kafka → Spark → MongoDB → Dashboard
          </div>

          <h1 className="hero-title">
            Real-Time Churn Streaming
            <span className="green"> with Auto-Recovery</span>
          </h1>

          <p className="hero-desc">
            A resilient data platform that ingests customer events from Kafka,
            processes using Spark Structured Streaming, stores results into MongoDB,
            and continuously monitors failures using a self-healing controller.
          </p>

          <div className="hero-kpis">
            <div className="kpi">
              <div className="kpi-label">Mongo Health</div>
              <div className="kpi-value">
                {health ? (
                  <span className={health.status === "ok" ? "ok" : "bad"}>
                    {health.status} ({health.mongo})
                  </span>
                ) : (
                  "Loading..."
                )}
              </div>
            </div>

            <div className="kpi">
              <div className="kpi-label">Total Scored Events</div>
              <div className="kpi-value">{stats ? stats.total : "Loading..."}</div>
            </div>

            <div className="kpi">
              <div className="kpi-label">Avg Churn Score</div>
              <div className="kpi-value">
                {stats && stats.avgChurnScore != null
                  ? `${stats.avgChurnScore}%`
                  : "—"}
              </div>
            </div>
          </div>

          {error && (
            <div className="neb-alert">
              <b>Error:</b> {error}
            </div>
          )}
        </div>

        <div className="hero-right">
          <div className="glass-panel">
            <div className="panel-title">Contract Type Distribution</div>
            <div className="panel-sub">
              Live summary from scored MongoDB events.
            </div>

            <div className="dist">
              {stats && stats.contractStats ? (
                stats.contractStats.map((c) => (
                  <div className="dist-row" key={c._id}>
                    <div className="dist-key">{c._id || "Unknown"}</div>
                    <div className="dist-bar">
                      <div
                        className="dist-fill"
                        style={{
                          width: `${Math.min(100, (c.count / Math.max(1, stats.total)) * 300)}%`,
                        }}
                      />
                    </div>
                    <div className="dist-val">{c.count}</div>
                  </div>
                ))
              ) : (
                <div className="loading">Loading…</div>
              )}
            </div>
          </div>

          <div className="glass-panel">
            <div className="panel-title">Churn Risk Distribution</div>
            <div className="panel-sub">ML model scoring every streaming event</div>
            <div className="dist">
              {stats && stats.riskStats ? (
                stats.riskStats.map((r) => {
                  const colors = {
                    CRITICAL: "#ff3b3b",
                    HIGH: "#ff8c00",
                    MEDIUM: "#ffd700",
                    LOW: "#18f3b0",
                  };
                  const color = colors[r._id] || "#8aa0a8";
                  return (
                    <div className="dist-row" key={r._id}>
                      <div className="dist-key" style={{ color }}>
                        {r._id || "Unknown"}
                      </div>
                      <div className="dist-bar">
                        <div
                          className="dist-fill"
                          style={{
                            width: `${Math.min(100, (r.count / Math.max(1, stats.total)) * 300)}%`,
                            background: color,
                            boxShadow: `0 0 16px ${color}55`,
                          }}
                        />
                      </div>
                      <div className="dist-val" style={{ color }}>
                        {r.count}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="loading">Loading…</div>
              )}
            </div>
          </div>

          <div className="mini-panels">
            <div className="mini">
              <div className="mini-icon">🧠</div>
              <div className="mini-title">Streaming Intelligence</div>
              <div className="mini-desc">Structured Streaming + schema validation</div>
            </div>
            <div className="mini">
              <div className="mini-icon">🛡️</div>
              <div className="mini-title">Self-Healing</div>
              <div className="mini-desc">Auto restart + health monitoring</div>
            </div>
            <div className="mini">
              <div className="mini-icon">📈</div>
              <div className="mini-title">Analytics</div>
              <div className="mini-desc">Contract split + churn insights</div>
            </div>
          </div>
        </div>
      </section>

      {/* ✅ LIVE MONITORING SECTION */}
      <section className="neb-section" id="pipeline">
        <div className="section-head">
          <h2>Live Monitoring</h2>
          <div className="section-actions">
            <button className="ghost-btn" onClick={loadAll}>Refresh</button>
          </div>
        </div>
        <MonitorPanel />
      </section>

      {/* TABLE */}
      <section className="neb-section" id="analytics">
        <div className="section-head">
          <h2>Latest Streaming Events</h2>
          <div className="section-actions">
            <input
              className="neb-input"
              placeholder="Search customer / contract…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <button className="ghost-btn" onClick={loadAll}>
              Refresh
            </button>
          </div>
        </div>

        <div className="table-wrap">
          <table className="neb-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Age</th>
                <th>Tenure</th>
                <th>Monthly Charges</th>
                <th>Contract</th>
                <th>Churn Score</th>
                <th>Risk</th>
                <th>Recommended Offer</th>
                <th>Event Time</th>
              </tr>
            </thead>
            <tbody>
  {filteredRows.map((r) => {
    const riskColors = {
      CRITICAL: "#ff3b3b",
      HIGH: "#ff8c00",
      MEDIUM: "#ffd700",
      LOW: "#18f3b0",
    };

    const rc = riskColors[r.risk_level] || "#8aa0a8";

    return (
      <tr key={r._id}>
        <td className="mono green">{r.customer_id || "N/A"}</td>

        <td>{r.age ?? 0}</td>
        <td>{r.tenure ?? 0}</td>

        {/* ✅ FIXED */}
        <td>${r.MonthlyCharges ?? 0}</td>

        {/* ✅ FIXED */}
        <td>
          <span className="pill">
            {r.Contract || "Month-to-month"}
          </span>
        </td>

        {/* ✅ FIXED */}
        <td className="mono">
          <span style={{ color: rc, fontWeight: 800 }}>
            {r.churn_probability != null
              ? `${r.churn_probability}%`
              : "0%"}
          </span>
        </td>

        {/* ✅ FIXED */}
        <td>
          <span
            className="risk-pill"
            style={{ borderColor: rc, color: rc }}
          >
            {r.risk_level || "LOW"}
          </span>
        </td>

        {/* ✅ FIXED */}
        <td style={{ fontSize: 12 }}>
          {r.offer || "Engagement SMS"}
        </td>

        {/* ✅ FIXED */}
        <td className="mono" style={{ fontSize: 12 }}>
          {r.ingest_time
            ? new Date(r.ingest_time).toLocaleTimeString()
            : "—"}
        </td>
      </tr>
    );
  })}
</tbody>
          </table>

          {!filteredRows.length && (
            <div className="empty">No results for your search.</div>
          )}
        </div>
      </section>

      {/* FOOTER */}
      <footer className="neb-footer">
        <div>
          <span className="green">CHURNAX</span> • Kafka + Spark + MongoDB • Self-Healing Controller
        </div>
        <div className="muted">© 2026 StreamLab</div>
      </footer>
    </div>
  );
}
