from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, VotingClassifier
from sklearn.impute import KNNImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, log_loss, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "age", "sex", "systolic_bp", "diastolic_bp", "resting_heart_rate",
    "body_temperature", "total_cholesterol", "ldl_cholesterol", "hdl_cholesterol",
    "blood_glucose", "serum_creatinine", "crp", "wbc_count", "pr_interval",
    "qt_interval", "qtc_interval", "heart_axis", "ejection_fraction", "ea_ratio",
    "wmsi", "bmi", "smoking_cigarettes", "alcohol_ml", "parent_disease",
]
NUMERIC_FEATURES = [feature for feature in FEATURE_NAMES if feature not in {"sex", "parent_disease"}]
MODEL_PATH = Path("models/heart_model.joblib")
DATASET_FEATURE_NAMES = [feature for feature in FEATURE_NAMES if feature != "sex"]
WORKBOOK_COLUMNS = {
    "Age": "age", "Systolic BP": "systolic_bp", "Diastolic BP": "diastolic_bp",
    "Resting Heart Rate": "resting_heart_rate", "Body Temperature F": "body_temperature",
    "Total Cholesterol": "total_cholesterol", "LDL Cholesterol": "ldl_cholesterol",
    "HDL Cholesterol": "hdl_cholesterol", "Blood Glucose": "blood_glucose",
    "Serum Creatinine": "serum_creatinine", "CRP mg per litre": "crp", "WBC Count": "wbc_count",
    "PR Interval ms": "pr_interval", "QT Interval ms": "qt_interval", "QTc Interval ms": "qtc_interval",
    "Heart Axis": "heart_axis", "Ejection Fraction pct": "ejection_fraction", "EA Ratio": "ea_ratio",
    "WMSI": "wmsi", "BMI": "bmi", "Smoking Cigarettes Per Day": "smoking_cigarettes",
    "Alcohol ml Per Day": "alcohol_ml", "Parent Disease": "parent_disease",
}
DISPLAY_NAMES = {
    "age": "Age", "systolic_bp": "Systolic BP", "diastolic_bp": "Diastolic BP",
    "resting_heart_rate": "Resting heart rate", "body_temperature": "Body temperature",
    "total_cholesterol": "Total cholesterol", "ldl_cholesterol": "LDL cholesterol",
    "hdl_cholesterol": "HDL cholesterol", "blood_glucose": "Blood glucose",
    "serum_creatinine": "Serum creatinine", "crp": "CRP", "wbc_count": "WBC count",
    "pr_interval": "PR interval", "qt_interval": "QT interval", "qtc_interval": "QTc interval",
    "heart_axis": "Heart axis", "ejection_fraction": "Ejection fraction", "ea_ratio": "E/A ratio",
    "wmsi": "WMSI", "bmi": "BMI", "smoking_cigarettes": "Smoking cigarettes",
    "alcohol_ml": "Alcohol intake", "parent_disease": "Parent disease history", "sex": "Sex",
}


def _make_pipeline():
    ensemble = VotingClassifier(
        estimators=[
            ("trees", ExtraTreesClassifier(n_estimators=500, min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1)),
            ("linear", Pipeline([("scale", StandardScaler()), ("logistic", LogisticRegression(max_iter=2000, class_weight="balanced"))])),
        ],
        voting="soft",
        weights=[2, 1],
    )
    return Pipeline([("impute", KNNImputer(n_neighbors=5)), ("model", ensemble)])


def train_model(csv_path="data/heart_disease.csv"):
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Add a labeled dataset at {path}.")

    frame = pd.read_excel(path) if path.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(path)
    if set(WORKBOOK_COLUMNS).issubset(frame.columns) and "Class" in frame.columns:
        frame = frame.rename(columns=WORKBOOK_COLUMNS)
        x = frame[DATASET_FEATURE_NAMES].apply(pd.to_numeric, errors="coerce")
        y = pd.to_numeric(frame["Class"], errors="coerce").astype(int)
        labels = frame[["Class", "Class Label"]].drop_duplicates().sort_values("Class")
        label_names = {int(row["Class"]): row["Class Label"] for _, row in labels.iterrows()}
    else:
        target_column = "target" if "target" in frame.columns else "heart_disease"
        missing = [column for column in FEATURE_NAMES + [target_column] if column not in frame.columns]
        if missing:
            raise ValueError(f"Dataset is missing columns: {', '.join(missing)}")
        frame = frame[FEATURE_NAMES + [target_column]].copy()
        frame["sex"] = frame["sex"].map({"Male": 1, "Female": 0, "M": 1, "F": 0}).fillna(frame["sex"])
        frame["parent_disease"] = frame["parent_disease"].map({"None": 0, "No": 0, "Yes": 1}).fillna(frame["parent_disease"])
        x = frame[FEATURE_NAMES].apply(pd.to_numeric, errors="coerce")
        y = pd.to_numeric(frame[target_column], errors="coerce").astype(int)
        label_names = {0: "Normal", 1: "Heart disease"}

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, stratify=y, random_state=42)
    pipeline = _make_pipeline()
    pipeline.fit(x_train, y_train)
    probabilities = pipeline.predict_proba(x_test)
    predictions = pipeline.predict(x_test)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, average="weighted", zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, predictions, average="weighted")), 4),
        "loss": round(float(log_loss(y_test, probabilities, labels=pipeline.classes_)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities, multi_class="ovr", labels=pipeline.classes_)), 4),
    }
    cross_val = cross_val_score(_make_pipeline(), x, y, cv=StratifiedKFold(5, shuffle=True, random_state=42), scoring="accuracy")
    metrics["cv_accuracy"] = round(float(cross_val.mean()), 4)
    report = classification_report(y_test, predictions, labels=pipeline.classes_, output_dict=True, zero_division=0)
    class_metrics = {
        str(int(class_id)): {
            "precision": round(float(report[str(class_id)]["precision"]), 4),
            "recall": round(float(report[str(class_id)]["recall"]), 4),
            "f1": round(float(report[str(class_id)]["f1-score"]), 4),
            "support": int(report[str(class_id)]["support"]),
        }
        for class_id in pipeline.classes_
    }
    tree_importance = pipeline.named_steps["model"].estimators_[0].feature_importances_
    importance_total = float(tree_importance.sum()) or 1.0
    feature_importance = {name: round(float(value / importance_total), 4) for name, value in zip(x.columns, tree_importance)}
    logistic = pipeline.named_steps["model"].named_estimators_["linear"].named_steps["logistic"]
    coefficients = logistic.coef_
    class_feature_importance = {}
    for index, class_id in enumerate(pipeline.classes_):
        coefficient_row = coefficients[index] if len(pipeline.classes_) > 2 else coefficients[0]
        absolute = np.abs(coefficient_row)
        total = float(absolute.sum()) or 1.0
        class_feature_importance[str(int(class_id))] = {name: round(float(value / total), 4) for name, value in zip(x.columns, absolute)}
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"pipeline": pipeline, "metrics": metrics, "class_metrics": class_metrics, "feature_names": list(x.columns, ), "label_names": label_names, "feature_importance": feature_importance, "class_feature_importance": class_feature_importance}, MODEL_PATH)
    return metrics


def _fallback_probability(values):
    score = 0.08
    score += max(0, values["age"] - 45) * 0.007
    score += max(0, values["systolic_bp"] - 120) * 0.004
    score += max(0, values["ldl_cholesterol"] - 100) * 0.0015
    score += max(0, values["bmi"] - 25) * 0.012
    score += max(0, values["smoking_cigarettes"] - 0) * 0.012
    score += 0.08 if values["parent_disease"] == 1 else 0
    return float(np.clip(score, 0.02, 0.94))


def predict_risk(payload):
    values = {}
    for name in FEATURE_NAMES:
        if name not in payload or payload[name] in ("", None):
            raise ValueError(f"Enter a value for {name.replace('_', ' ')}.")
        if name == "sex":
            values[name] = 1 if str(payload[name]).lower() in {"male", "m", "1"} else 0
        elif name == "parent_disease":
            values[name] = 0 if str(payload[name]).lower() in {"none", "no", "0"} else 1
        else:
            values[name] = float(payload[name])

    if MODEL_PATH.exists():
        bundle = joblib.load(MODEL_PATH)
        feature_names = bundle.get("feature_names", FEATURE_NAMES)
        row = pd.DataFrame([{name: values[name] for name in feature_names}], columns=feature_names)
        probabilities = bundle["pipeline"].predict_proba(row)[0]
        classes = bundle["pipeline"].classes_
        predicted_class = int(classes[int(np.argmax(probabilities))])
        label_names = bundle.get("label_names", {})
        disease = label_names.get(predicted_class, "Heart disease")
        probability = float(1 - probabilities[list(classes).index(0)]) if 0 in classes and predicted_class != 0 else float(np.max(probabilities))
        model_metrics = bundle.get("class_metrics", {}).get(str(predicted_class), bundle.get("metrics", {})).copy()
        model_metrics["accuracy"] = bundle.get("metrics", {}).get("accuracy")
        model_metrics["loss"] = bundle.get("metrics", {}).get("loss")
        importance = bundle.get("class_feature_importance", {}).get(str(predicted_class), bundle.get("feature_importance", {}))
        based_on = [
            {"name": DISPLAY_NAMES.get(name, name.replace("_", " ").title()), "value": round(values[name], 2), "importance": round(score * 100, 1)}
            for name, score in sorted(importance.items(), key=lambda item: item[1], reverse=True)[:5]
        ]
        class_probabilities = [
            {"name": label_names.get(int(class_id), f"Class {class_id}"), "probability": round(float(score) * 100, 1)}
            for class_id, score in sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)
        ]
        source = "trained model"
    else:
        probability = _fallback_probability(values)
        disease = "Heart disease" if probability >= 0.5 else "Normal"
        based_on = []
        class_probabilities = [{"name": disease, "probability": round(probability * 100, 1)}]
        model_metrics = {}
        source = "screening estimate"

    risk = "higher" if probability >= 0.5 else "lower"
    return {
        "probability": round(probability * 100, 1),
        "disease": disease,
        "based_on": based_on,
        "class_probabilities": class_probabilities,
        "risk": risk,
        "source": source,
        "metrics": model_metrics,
        "message": "This result is a screening aid, not a diagnosis. Seek urgent medical care for severe or sudden symptoms.",
    }
