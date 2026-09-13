"""Create a reproducible synthetic training dataset for local development.

This is not clinical data and must not be used for medical decisions. Replace it
with an approved real-world dataset before evaluating clinical performance.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from model import FEATURE_NAMES


SEED = 42
SAMPLES = 3000


def build_dataset(samples=SAMPLES, seed=SEED):
    rng = np.random.default_rng(seed)
    age = rng.integers(18, 91, samples)
    sex = rng.choice(["Male", "Female"], samples)
    systolic_bp = np.clip(rng.normal(126 + (age - 45) * 0.35, 18, samples), 90, 200)
    diastolic_bp = np.clip(rng.normal(79 + (age - 45) * 0.12, 11, samples), 60, 130)
    resting_heart_rate = np.clip(rng.normal(74, 13, samples), 40, 160)
    body_temperature = np.clip(rng.normal(98.6, 0.55, samples), 96.8, 105.0)
    total_cholesterol = np.clip(rng.normal(190 + (age - 45) * 0.4, 38, samples), 103.4, 349.7)
    ldl_cholesterol = np.clip(rng.normal(112 + (age - 45) * 0.25, 29, samples), 40, 242)
    hdl_cholesterol = np.clip(rng.normal(54, 13, samples), 20, 100)
    blood_glucose = np.clip(rng.normal(102 + (age - 45) * 0.15, 28, samples), 60, 248.2)
    serum_creatinine = np.clip(rng.normal(1.0, 0.32, samples), 0.4, 2.97)
    crp = np.clip(rng.lognormal(np.log(2.4), 0.7, samples), 0.1, 40.88)
    wbc_count = np.clip(rng.normal(7.1, 1.8, samples), 3, 20)
    pr_interval = np.clip(rng.normal(178, 25, samples), 120, 300)
    qt_interval = np.clip(rng.normal(390, 35, samples), 280, 550)
    qtc_interval = np.clip(qt_interval + rng.normal(30, 18, samples), 300, 580)
    heart_axis = np.clip(rng.normal(45, 38, samples), -90, 180)
    ejection_fraction = np.clip(rng.normal(60 - (age - 50) * 0.06, 9, samples), 15, 80)
    ea_ratio = np.clip(rng.normal(1.05, 0.35, samples), 0.3, 2.08)
    wmsi = np.clip(rng.normal(1.0, 0.16, samples), 1, 2.67)
    bmi = np.clip(rng.normal(27, 5.2, samples), 15, 49.7)
    smoking_cigarettes = np.clip(rng.poisson(3.5, samples), 0, 30)
    alcohol_ml = np.clip(rng.gamma(1.7, 28, samples), 0, 300)
    parent_disease = rng.choice(["None", "Yes"], samples, p=[0.68, 0.32])

    latent_score = (
        -3.9
        + (age - 45) * 0.035
        + (systolic_bp - 120) * 0.018
        + (total_cholesterol - 180) * 0.008
        + (ldl_cholesterol - 100) * 0.012
        - (hdl_cholesterol - 50) * 0.018
        + (blood_glucose - 100) * 0.009
        + (crp - 2) * 0.025
        + (bmi - 25) * 0.045
        + smoking_cigarettes * 0.045
        + (ejection_fraction < 50) * 0.9
        + (wmsi - 1) * 1.8
        + (parent_disease == "Yes") * 0.65
        + rng.normal(0, 0.45, samples)
    )
    probability = 1 / (1 + np.exp(-latent_score))
    target = (rng.random(samples) < probability).astype(int)

    frame = pd.DataFrame({
        "age": age, "sex": sex, "systolic_bp": systolic_bp, "diastolic_bp": diastolic_bp,
        "resting_heart_rate": resting_heart_rate, "body_temperature": body_temperature,
        "total_cholesterol": total_cholesterol, "ldl_cholesterol": ldl_cholesterol,
        "hdl_cholesterol": hdl_cholesterol, "blood_glucose": blood_glucose,
        "serum_creatinine": serum_creatinine, "crp": crp, "wbc_count": wbc_count,
        "pr_interval": pr_interval, "qt_interval": qt_interval, "qtc_interval": qtc_interval,
        "heart_axis": heart_axis, "ejection_fraction": ejection_fraction, "ea_ratio": ea_ratio,
        "wmsi": wmsi, "bmi": bmi, "smoking_cigarettes": smoking_cigarettes,
        "alcohol_ml": alcohol_ml, "parent_disease": parent_disease, "target": target,
    })
    return frame[FEATURE_NAMES + ["target"]]


if __name__ == "__main__":
    output = Path("data/heart_disease.csv")
    output.parent.mkdir(exist_ok=True)
    dataset = build_dataset()
    dataset.to_csv(output, index=False)
    print(f"Created {output} with {len(dataset)} rows")
    print(dataset["target"].value_counts().sort_index().to_string())
