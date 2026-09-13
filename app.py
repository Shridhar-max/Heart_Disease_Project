from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request

from model import FEATURE_NAMES, predict_risk, train_model

app = Flask(__name__)


@app.get("/")
def home():
    return redirect("/register")


@app.get("/predict")
def predict_page():
    return render_template("index.html", features=FEATURE_NAMES)


@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.get("/login")
def login():
    return render_template("login.html")


@app.get("/register")
def register():
    return render_template("register.html")


@app.post("/api/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    try:
        result = predict_risk(payload)
        return jsonify(result)
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "model": "ExtraTrees + LogisticRegression ensemble"})


if __name__ == "__main__":
    model_path = Path("models/heart_model.joblib")
    dataset_path = Path("data/heart_disease.csv")
    if not model_path.exists() and dataset_path.exists():
        train_model()
    app.run(debug=True, port=5000)
