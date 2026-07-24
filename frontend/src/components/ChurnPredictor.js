import React, { useState, useEffect } from "react";

const ChurnPredictor = () => {
  const [prediction, setPrediction] = useState(null);

  const sampleCustomer = {
    tenure: 12,
    MonthlyCharges: 70,
    Contract: "Month-to-month",
  };

  const fetchPrediction = async () => {
    try {
      const res = await fetch("http://localhost:5000/predict-churn", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(sampleCustomer),
      });

      const data = await res.json();
      setPrediction(data);
    } catch (err) {
      console.error("Error:", err);
    }
  };

  // 🔥 AUTO REFRESH EVERY 5 SEC
  useEffect(() => {
    fetchPrediction();
    const interval = setInterval(fetchPrediction, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h2>🔮 Churn Prediction</h2>

      {prediction ? (
        <div
          style={{
            background: "#111",
            padding: "20px",
            borderRadius: "10px",
            color: "white",
            width: "300px",
          }}
        >
          <h3>Risk: {prediction.risk_level}</h3>
          <p>Probability: {prediction.churn_probability}%</p>
          <p>Offer: {prediction.offer.name}</p>
        </div>
      ) : (
        <p>Loading prediction...</p>
      )}
    </div>
  );
};

export default ChurnPredictor;