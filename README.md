# AI Patient Triage Assistant
### BSc Computer Engineering — AI in Engineering Project
---

## Problem Statement
Ghanaian clinics, especially rural CHPS compounds and district hospitals, face severe
staff shortages. Patients queue regardless of urgency, and critical cases sometimes
worsen while waiting. This AI system helps nurses quickly assess and prioritize patients.

## Solution
A machine learning web app that:
- Takes patient symptoms as input
- Predicts urgency level: HIGH / MEDIUM / LOW
- Suggests the likely condition
- Displays confidence scores

---

## Project Structure
```
triage-assistant/
├── app.py              # Streamlit web application
├── model.py            # Model training script
├── preprocess.py       # Data cleaning & NLP pipeline
├── download_data.py    # Dataset downloader
├── requirements.txt    # Python dependencies
├── data/
│   └── dataset.csv     # Training data (after download)
└── model/
    ├── triage_model.pkl    # Trained urgency model
    └── disease_model.pkl   # Trained disease model
```

---

## Setup & Run (Step by Step)

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Download the dataset
```bash
python download_data.py
```

### Step 3 — Train the models
```bash
python model.py
```

### Step 4 — Run the app
```bash
streamlit run app.py
```
Then open your browser at: **http://localhost:8501**

---

## Tech Stack
| Component       | Technology                        |
|----------------|-----------------------------------|
| Language        | Python 3.10+                     |
| ML Framework    | Scikit-learn                     |
| NLP             | NLTK (TF-IDF, lemmatization)     |
| Web App         | Streamlit                        |
| Models Used     | Random Forest, Logistic Regression|

---

## Team
BSc Computer Engineering — [Your University Name]
Course: AI in Engineering

---

## Repository
GitHub: https://github.com/joeAnnan/triage-assistant

---

## Streamlit Deployment

To deploy this app to Streamlit Cloud:

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Configure:
   - Repository: `joeAnnan/triage-assistant`
   - Branch: `main`
   - Main file path: `app.py`
5. Click **"Deploy"**

The app will automatically train models on first deployment if the `.pkl` files are not present.

---

## Disclaimer
This is an academic prototype and does NOT replace professional medical diagnosis.
