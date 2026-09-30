import os
from datetime import datetime

import pandas as pd
import streamlit as st

from model import ensure_models
from preprocess import clean_symptom_text, URGENCY_COLORS, URGENCY_ADVICE
from security import (
    sanitize_input,
    encrypt_record,
    decrypt_record,
    ENC_HISTORY,
)

st.set_page_config(
    page_title="Patient Triage Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
html, body, [class*="css"] {
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}
.block-container {
  padding-top: 1rem;
  padding-bottom: 2rem;
  padding-left: 1rem;
  padding-right: 1rem;
  max-width: 920px;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.main-header {
  background: linear-gradient(135deg, #1a5276, #2e86c1);
  padding: 1.1rem 1.15rem;
  border-radius: 12px;
  color: white;
  margin-bottom: 1rem;
}
.main-header h1 {
  margin: 0;
  font-size: 1.45rem;
  line-height: 1.25;
  font-weight: 700;
}
.main-header p {
  margin: 0.35rem 0 0;
  font-size: 0.92rem;
  opacity: 0.95;
  line-height: 1.4;
}
.result-card {
  padding: 1rem 1.1rem;
  border-radius: 12px;
  border-left: 6px solid;
  margin: 0.75rem 0;
}
.result-high { border-color: #e74c3c; background: #fdf2f2; }
.result-medium { border-color: #f39c12; background: #fef9f0; }
.result-low { border-color: #27ae60; background: #f0faf4; }
.metric-box, .stat-box, .record-card {
  background: white;
  border-radius: 10px;
  padding: 0.85rem 1rem;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
}
.metric-box { text-align: center; }
.stat-box { text-align: center; border-top: 4px solid; }
.record-card { margin-bottom: 0.7rem; border: 1px solid #eef2f6; }
.symptom-tag {
  display: inline-block;
  background: #eaf2ff;
  color: #1a5276;
  padding: 4px 10px;
  border-radius: 16px;
  margin: 3px 3px 0 0;
  font-size: 0.82rem;
}
.disclaimer {
  background: #fff8e8;
  border: 1px solid #e6c36a;
  border-radius: 8px;
  padding: 0.75rem 0.9rem;
  font-size: 0.85rem;
  color: #5c4a12;
  margin-top: 0.9rem;
  line-height: 1.45;
}
.priority-high { color: #e74c3c; font-weight: 700; }
.priority-medium { color: #d68910; font-weight: 700; }
.priority-low { color: #1e8449; font-weight: 700; }

@media (min-width: 768px) {
  .block-container {
    padding-top: 1.5rem;
    padding-left: 2rem;
    padding-right: 2rem;
  }
  .main-header {
    padding: 1.6rem 1.8rem;
  }
  .main-header h1 { font-size: 1.9rem; }
}

@media (max-width: 640px) {
  .block-container {
    padding-left: 0.5rem;
    padding-right: 0.5rem;
  }
  .main-header {
    padding: 0.9rem 1rem;
  }
  .main-header h1 {
    font-size: 1.3rem;
  }
  .main-header p {
    font-size: 0.85rem;
  }
  div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  div[data-testid="column"] {
    min-width: 100% !important;
    width: 100% !important;
    flex: 1 1 100% !important;
  }
  .stButton > button {
    width: 100%;
    min-height: 2.7rem;
    font-size: 0.95rem;
  }
  textarea {
    min-height: 96px !important;
    font-size: 0.95rem;
  }
  .metric-box, .stat-box {
    padding: 0.7rem 0.8rem;
  }
  .result-card {
    padding: 0.8rem 0.9rem;
  }
  .symptom-tag {
    font-size: 0.78rem;
    padding: 3px 8px;
  }
}
</style>
""",
    unsafe_allow_html=True,
)

COMMON_SYMPTOMS = [
    "fever", "headache", "vomiting", "nausea", "chills", "fatigue", "sweating", "body ache",
    "diarrhea", "cough", "sore throat", "chest pain", "difficulty breathing", "skin rash",
    "itching", "abdominal pain", "loss of appetite", "dizziness", "yellow eyes", "joint pain",
    "runny nose", "back pain", "weakness", "weight loss", "blurred vision", "high temperature",
    "swollen lymph nodes", "stiff neck",
]


def save_to_history(recorded_by, name, age, sex, symptoms, duration, urgency, condition):
    record = {
        "Timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "Name": name or "Unknown",
        "Age": age,
        "Sex": sex,
        "Symptoms": symptoms,
        "Duration": duration,
        "Urgency": urgency,
        "Condition": condition,
        "RecordedBy": recorded_by or "",
    }
    encrypted = encrypt_record(record)
    df_new = pd.DataFrame([encrypted])
    if os.path.exists(ENC_HISTORY):
        df_combined = pd.concat([pd.read_csv(ENC_HISTORY), df_new], ignore_index=True)
    else:
        df_combined = df_new
    df_combined.to_csv(ENC_HISTORY, index=False)


def load_history():
    if not os.path.exists(ENC_HISTORY):
        return pd.DataFrame()
    df = pd.read_csv(ENC_HISTORY)
    if df.empty:
        return df
    decrypted_rows = [decrypt_record(row) for row in df.to_dict("records")]
    return pd.DataFrame(decrypted_rows)


@st.cache_resource
def load_models():
    return ensure_models()

@st.cache_data(ttl=300)
def get_history_stats():
    history_df = load_history()
    if history_df.empty:
        return 0, 0, 0, 0
    total = len(history_df)
    high = int((history_df["Urgency"] == "HIGH").sum()) if "Urgency" in history_df.columns else 0
    medium = int((history_df["Urgency"] == "MEDIUM").sum()) if "Urgency" in history_df.columns else 0
    low = int((history_df["Urgency"] == "LOW").sum()) if "Urgency" in history_df.columns else 0
    return total, high, medium, low

def run_prediction(symptom_text):
    um, dm = load_models()
    cleaned = clean_symptom_text(symptom_text)
    urgency = um.predict([cleaned])[0]
    disease = dm.predict([cleaned])[0]
    proba = um.predict_proba([cleaned])[0]
    return urgency, disease.title(), dict(zip(um.classes_, proba))


st.markdown(
    '<div class="main-header"><h1>Patient Triage Assistant</h1>'
    "<p>Enter patient symptoms to determine urgency level and possible condition. "
    "This is a support tool - clinical assessment should always come first.</p></div>",
    unsafe_allow_html=True,
)

tab_assess, tab_records = st.tabs(["Assess patient", "Patient records"])

with tab_assess:
    st.subheader("Patient details")
    patient_name = st.text_input("Full name", placeholder="e.g. Kofi Mensah")
    age_col, sex_col = st.columns(2)
    with age_col:
        patient_age = st.number_input("Age (years)", min_value=0, max_value=120, value=25)
    with sex_col:
        patient_sex = st.selectbox("Sex", ["Female", "Male", "Other"])
    recorded_by = st.text_input("Recorded by (optional)", placeholder="Your name")

    st.subheader("Presenting symptoms")
    selected_symptoms = st.multiselect(
        "Select all that apply",
        COMMON_SYMPTOMS,
        format_func=lambda s: s.capitalize(),
    )
    typed_symptoms = st.text_area(
        "Additional notes",
        placeholder="e.g. high fever and vomiting for 3 days",
        height=90,
    )
    all_symptoms = (" ".join(selected_symptoms) + " " + (typed_symptoms or "")).strip()

    duration = st.select_slider(
        "How long have the symptoms lasted?",
        options=["< 1 hour", "1-6 hours", "6-24 hours", "1-3 days", "3-7 days", "> 1 week"],
        value="1-3 days",
    )

    assess_clicked = st.button("Assess patient", type="primary", use_container_width=True)

    if assess_clicked:
        name_check = sanitize_input(patient_name, "Patient name")
        sym_check = sanitize_input(all_symptoms, "Symptoms")

        if not name_check["valid"]:
            st.error(name_check["warning"])
        elif not sym_check["valid"]:
            st.error(sym_check["warning"])
        elif not all_symptoms:
            st.warning("Enter at least one symptom.")
        else:
            clean_name = name_check["clean_text"]
            clean_syms = sym_check["clean_text"]
            with st.spinner("Analyzing symptoms..."):
                urgency, condition, confidence = run_prediction(clean_syms or all_symptoms)

            save_to_history(
                recorded_by,
                clean_name,
                patient_age,
                patient_sex,
                ", ".join(selected_symptoms) if selected_symptoms else clean_syms,
                duration,
                urgency,
                condition,
            )

            color = URGENCY_COLORS[urgency]
            advice = URGENCY_ADVICE[urgency]
            st.markdown(
                f'<div class="result-card result-{urgency.lower()}">'
                f'<h2 style="color:{color};margin:0">{urgency} PRIORITY</h2>'
                f'<p style="margin:0.45rem 0 0">{advice}</p></div>',
                unsafe_allow_html=True,
            )

            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(
                    f'<div class="metric-box"><div style="font-size:0.78rem;color:#777">PATIENT</div>'
                    f'<div style="font-size:1.1rem;font-weight:600">{clean_name or "Unknown"}</div>'
                    f'<div style="font-size:0.85rem;color:#555">{patient_age} yrs · {patient_sex}</div></div>',
                    unsafe_allow_html=True,
                )
            with m2:
                st.markdown(
                    f'<div class="metric-box"><div style="font-size:0.78rem;color:#777">POSSIBLE CONDITION</div>'
                    f'<div style="font-size:1.1rem;font-weight:600">{condition}</div>'
                    f'<div style="font-size:0.85rem;color:#555">Requires clinical review</div></div>',
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f'<div class="metric-box"><div style="font-size:0.78rem;color:#777">DURATION</div>'
                    f'<div style="font-size:1.1rem;font-weight:600">{duration}</div>'
                    f'<div style="font-size:0.85rem;color:#555">As reported</div></div>',
                    unsafe_allow_html=True,
                )

            st.markdown("##### Assessment breakdown")
            conf_df = pd.DataFrame({
                "Urgency Level": list(confidence.keys()),
                "Score (%)": [round(v * 100, 1) for v in confidence.values()],
            }).sort_values("Score (%)", ascending=False)
            st.bar_chart(conf_df.set_index("Urgency Level"), height=180)

            if selected_symptoms:
                st.markdown("##### Symptoms recorded")
                st.markdown(
                    "".join([f'<span class="symptom-tag">{s}</span>' for s in selected_symptoms]),
                    unsafe_allow_html=True,
                )

            st.success("Record saved.")
            st.markdown(
                '<div class="disclaimer"><strong>Note:</strong> This tool assists with triage. '
                "It does not replace patient examination, tests, or clinical judgment.</div>",
                unsafe_allow_html=True,
            )

with tab_records:
    st.subheader("Saved assessments")
    history_df = load_history()

    if history_df.empty:
        st.info("No records yet. Assess a patient to create the first entry.")
    else:
        total, high, medium, low = get_history_stats()

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(
                f'<div class="stat-box" style="border-color:#2e86c1">'
                f'<div style="font-size:0.75rem;color:#777">TOTAL</div>'
                f'<div style="font-size:1.7rem;font-weight:700;color:#2e86c1">{total}</div></div>',
                unsafe_allow_html=True,
            )
        with s2:
            st.markdown(
                f'<div class="stat-box" style="border-color:#e74c3c">'
                f'<div style="font-size:0.75rem;color:#777">HIGH</div>'
                f'<div style="font-size:1.7rem;font-weight:700;color:#e74c3c">{high}</div></div>',
                unsafe_allow_html=True,
            )
        with s3:
            st.markdown(
                f'<div class="stat-box" style="border-color:#f39c12"'
                f'<div style="font-size:0.75rem;color:#777">MEDIUM</div>'
                f'<div style="font-size:1.7rem;font-weight:700;color:#f39c12">{medium}</div></div>',
                unsafe_allow_html=True,
            )
        with s4:
            st.markdown(
                f'<div class="stat-box" style="border-color:#27ae60"'
                f'<div style="font-size:0.75rem;color:#777">LOW</div>'
                f'<div style="font-size:1.7rem;font-weight:700;color:#27ae60">{low}</div></div>',
                unsafe_allow_html=True,
            )

        filter_urgency = st.selectbox("Urgency", ["All", "HIGH", "MEDIUM", "LOW"])
        search_name = st.text_input("Search by name")

        filtered = history_df.copy()
        if filter_urgency != "All":
            filtered = filtered[filtered["Urgency"] == filter_urgency]
        if search_name:
            filtered = filtered[filtered["Name"].str.contains(search_name, case=False, na=False)]

        st.caption(f"{len(filtered)} record(s)")
        for _, row in filtered.iloc[::-1].iterrows():
            urgency = str(row.get("Urgency", ""))
            cls = {"HIGH": "priority-high", "MEDIUM": "priority-medium", "LOW": "priority-low"}.get(
                urgency, ""
            )
            symptoms = row.get("Symptoms", "")
            recorded = row.get("RecordedBy") or row.get("AssessedBy") or ""
            extra = f" · {recorded}" if recorded else ""
            st.markdown(
                f'<div class="record-card">'
                f'<div style="display:flex;justify-content:space-between;gap:0.6rem;flex-wrap:wrap">'
                f"<strong>{row.get('Name', '')}</strong>"
                f'<span class="{cls}">{urgency}</span></div>'
                f'<div style="font-size:0.85rem;color:#555;margin-top:0.25rem">'
                f"{row.get('Age', '')} yrs · {row.get('Sex', '')} · {row.get('Duration', '')}{extra}</div>'
                f'<div style="margin-top:0.4rem;font-size:0.9rem">{symptoms}</div>'
                f'<div style="margin-top:0.35rem;font-size:0.85rem"><strong>Possible condition:</strong> {row.get("Condition", "")}</div>'
                f'<div style="margin-top:0.2rem;font-size:0.78rem;color:#777">{row.get("Timestamp", "")}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        st.download_button(
            "Download records (CSV)",
            filtered.to_csv(index=False).encode(),
            f"triage_records_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True,
        )
