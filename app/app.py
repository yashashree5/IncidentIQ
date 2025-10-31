import os
import pandas as pd
import psycopg2
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# --- OpenAI client (SDK v1.x) ---
try:
    from openai import OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    client = None

st.set_page_config(page_title="IncidentIQ | AI-Powered Ops Dashboard", layout="wide")
st.title("IncidentIQ – AI-Powered Incident Management Dashboard")

# ---------------- DB CONFIG ----------------
PG = dict(
    host=os.getenv("PGHOST", "localhost"),  # if running locally
    port=int(os.getenv("PGPORT", "5434")),  # match your docker-compose mapping
    dbname=os.getenv("POSTGRES_DB", "incidentdb"),
    user=os.getenv("POSTGRES_USER", "incident"),
    password=os.getenv("POSTGRES_PASSWORD", "incidentpw"),
)

@st.cache_data(ttl=300)
def load_incidents():
    conn = psycopg2.connect(**PG)
    df = pd.read_sql("select * from analytics.fct_incidents", conn)
    conn.close()
    return df

df = load_incidents()

# ---------------- TOP KPIs ----------------
k1, k2, k3 = st.columns(3)
k1.metric("Total Incidents", len(df))
k2.metric("Avg MTTR (hrs)", round(df["mttr_hours"].mean(), 2) if len(df) else 0)
k3.metric("SLA Compliance (%)", round(df["sla_met_by_priority"].mean()*100, 2) if len(df) else 0)

# ---------------- FILTERS ----------------
with st.expander("Filters", expanded=True):
    priorities = sorted([int(x) for x in df["priority"].dropna().unique()])
    sel_pri = st.multiselect("Priority", options=priorities, default=priorities)
    date_min = pd.to_datetime(df["opened_at"]).min()
    date_max = pd.to_datetime(df["opened_at"]).max()
    sel_range = st.date_input("Opened between", value=(date_min.date(), date_max.date()))

# apply filters
fdf = df.copy()
if sel_pri:
    fdf = fdf[fdf["priority"].isin(sel_pri)]
if isinstance(sel_range, (list, tuple)) and len(sel_range) == 2:
    start, end = pd.to_datetime(sel_range[0]), pd.to_datetime(sel_range[1]) + pd.Timedelta(days=1)
    fdf = fdf[(pd.to_datetime(fdf["opened_at"]) >= start) & (pd.to_datetime(fdf["opened_at"]) < end)]

# ---------------- CHARTS ----------------
st.subheader("Volume by Priority")
vol = fdf.groupby("priority")["incident_id"].count().reset_index().rename(columns={"incident_id":"count"})
st.bar_chart(vol, x="priority", y="count")

st.subheader("Average MTTR by Priority (hrs)")
mttr = fdf.groupby("priority")["mttr_hours"].mean().reset_index()
st.bar_chart(mttr, x="priority", y="mttr_hours")

# ---------------- TABLE + SELECTION ----------------
st.subheader("Recent Incidents")
fdf_display = fdf.sort_values("opened_at", ascending=False).head(200)
st.dataframe(fdf_display, use_container_width=True)

# simple selector
incident_ids = fdf_display["incident_id"].astype(str).tolist()
sel_incident = st.selectbox("Pick an incident to triage", incident_ids)

# ---------------- AI TRIAGE ----------------
st.markdown("---")
st.header("🤖 AI Triage")

def build_prompt(row: pd.Series) -> str:
    sev = "P1" if row.get("priority") == 1 else ("P2" if row.get("priority") == 2 else "P3")
    # keep it compact; all values become strings for safety
    payload = {
        "incident_id": str(row.get("incident_id")),
        "opened_at": str(row.get("opened_at")),
        "created_at": str(row.get("created_at")),
        "first_resolved_at": str(row.get("first_resolved_at")),
        "closed_at": str(row.get("closed_at")),
        "last_state": str(row.get("last_state")),
        "priority": int(row.get("priority")) if pd.notna(row.get("priority")) else None,
        "impact": int(row.get("impact")) if pd.notna(row.get("impact")) else None,
        "urgency": int(row.get("urgency")) if pd.notna(row.get("urgency")) else None,
        "category": str(row.get("category")),
        "subcategory": str(row.get("subcategory")),
        "assignment_group": str(row.get("assignment_group")),
        "made_sla": bool(row.get("made_sla")) if pd.notna(row.get("made_sla")) else None,
        "mttr_hours": float(row.get("mttr_hours")) if pd.notna(row.get("mttr_hours")) else None,
        "mttd_hours": float(row.get("mttd_hours")) if pd.notna(row.get("mttd_hours")) else None,
        "sla_met_by_priority": bool(row.get("sla_met_by_priority")) if pd.notna(row.get("sla_met_by_priority")) else None,
        "severity_suggestion": sev,
    }
    return f"""
You are an SRE incident triage assistant.
Return STRICT JSON with keys: summary, likely_root_causes, remediations, severity, next_actions.
- Keep summary <= 6 lines and specific.
- Severity must be P1, P2, or P3 (map from priority 1→P1, 2→P2, else P3).
- Give 3–6 concise remediation steps (imperative voice).
- If data is missing, note it; do not invent specifics.
Return ONLY JSON.

Incident:
{payload}
"""

triage_col, json_col = st.columns([1,1.2])

with triage_col:
    st.write("**Selected incident:**", sel_incident)
    triage_btn = st.button("Triage with AI", type="primary", disabled=(client is None or sel_incident is None))
    if client is None:
        st.info("Set your OPENAI_API_KEY in the environment before using AI triage.")

result_box = None
if triage_btn and sel_incident:
    row = fdf[fdf["incident_id"].astype(str) == sel_incident].iloc[0]
    prompt = build_prompt(row)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=400,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You return JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        import json
        content = resp.choices[0].message.content
        parsed = json.loads(content)
        result_box = parsed
    except Exception as e:
        st.error(f"LLM error: {e}")

with json_col:
    st.subheader("AI Output")
    if result_box:
        st.write("**Summary**")
        st.write(result_box.get("summary"))
        st.write("**Likely Root Causes**")
        st.write(result_box.get("likely_root_causes"))
        st.write("**Remediations**")
        st.write(result_box.get("remediations"))
        st.write("**Severity**:", result_box.get("severity"))
        st.write("**Next Actions**")
        st.write(result_box.get("next_actions"))
    else:
        st.caption("Click **Triage with AI** to generate analysis for the selected incident.")

st.markdown("<hr><center><small>Built with ❤️ by Yashashree Shinde | IncidentIQ</small></center>", unsafe_allow_html=True)
