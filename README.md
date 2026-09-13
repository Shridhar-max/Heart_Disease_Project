# HeartPredict

A Flask + vanilla JavaScript heart-disease screening interface based on the supplied reference design.

## Run

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

Open http://127.0.0.1:5000.

## Train the model

The provided workbook is already copied to `data/heart_disease_25k_encoded_1.xlsx`. It contains 25,000 rows and seven classes: Normal, Arrhythmia, Cardiovascular Disease, Coronary Artery, Congenital Heart Disease, Cardiomyopathy, and Heart Infections. Train from it with:

```powershell
py -c "from model import train_model; print(train_model(r'data/heart_disease_25k_encoded_1.xlsx'))"
```

The trainer maps the workbook headers, supports its seven-class target, and ignores `Sex` during training because the workbook does not contain that column. The form still collects sex for future datasets that include it.

For a synthetic local demo dataset, use `py generate_dataset.py` and then train from `data/heart_disease.csv`.

To train from your own labeled CSV, use:

```powershell
py -c "from model import train_model; print(train_model())"
```

The pipeline uses KNN imputation and a soft-voting ExtraTrees + logistic regression ensemble. It prints held-out accuracy, weighted F1, multiclass ROC-AUC, and 5-fold cross-validation accuracy. The UI returns the predicted disease class and probability. These metrics are dataset metrics, not proof of clinical performance.
