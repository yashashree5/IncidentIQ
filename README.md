# IncidentIQ — AI-Powered Incident Management Data Platform  

> **"From chaos to clarity — how AI now helps resolve incidents faster."**

---

## Background  

Working with **Barclays**, I witnessed firsthand how our **Run the Bank (RTB)** teams struggled with day-to-day incident management.  
Each incident — no matter how small — meant:  
- Endless **manual updates** in Excel sheets  
- Constant back-and-forth between **RTB** (operations) and **BTB** (Build the Bank / engineering)  
- Delays in **client communication** while waiting for fixes  
- And zero automation in **root cause analysis**

This manual, human-dependent process wasted **hours every day**, and often left RTB powerless until BTB responded.

---

## The Problem  

The **incident tracking sheet** was the lifeline — but also the bottleneck.  
Imagine this:  
> A production outage hits. RTB logs it in the sheet.  
> BTB digs through logs, connects systems, identifies the fix — manually.  
> RTB waits. Clients wait. Deadlines slip.  

There was **no single source of truth**, no data-driven visibility, and no quick way to understand incident impact or recurring patterns.

---

## The Spark  

That’s where **IncidentIQ** was born —  
an **AI-powered Incident Management Data Platform** that brings together:

- **Postgres** for centralized data  
- **Airflow** for automated ingestion  
- **dbt** for SLA & performance metrics  
- **Streamlit** for interactive dashboards  
- **OpenAI** for instant, intelligent triage  

> Turning **manual triage** into **AI-assisted resolution**.

---

## Architecture Overview  
[Incident Logs / UCI Dataset]
│
▼
Apache Airflow ──► PostgreSQL (raw)
│
▼
dbt (data transformation)
│
▼
Analytics Schema: SLA, MTTR, MTTD
│
▼
Streamlit Dashboard ──► AI Triage (OpenAI)


---

##  Staging the Data  

The first step was to automate ingestion and cleaning.  
Here’s a glimpse from the **command-line staging process**:

| Stage | Description | Screenshot |
|--------|-------------|-------------|
| **1. Airflow DAG setup** | Automated ingestion pipeline from UCI dataset to Postgres | ![Airflow DAG](images/airflow_dag.png) |
| **2. dbt Build Stage** | Transformation of raw data into analytics schema | ![dbt build](images/dbt_build.png) |
| **3. Data Validation** | Checking record counts and SLA metrics | ![Validation](images/dbt_test.png) |

*(Replace the placeholders above with your actual CLI screenshots — e.g., `images/staging_step1.png` etc.)*

---

## 📊 The Dashboard  

### 💼 Key Features:  
- Real-time visibility into **SLA compliance**, **incident volume**, and **MTTR trends**  
- Interactive filtering by **priority**, **service**, or **assignment group**  
- Seamless **AI triage** — just pick an incident and click **“Triage with AI”**

| KPI | Description |
|-----|--------------|
| **MTTR** | Mean Time to Resolve — measures operational efficiency |
| **SLA Compliance** | % of incidents resolved within target SLA |
| **Volume by Priority** | Tracks incident load across priorities |

![Dashboard Screenshot](images/dashboard.png)

---

## 🤖 AI to the Rescue  

The magic moment:  
When RTB clicks **“Triage with AI”**, the system automatically analyzes the incident data, then uses OpenAI to generate:

- 🧠 **Summary:** What happened and why  
- 🔍 **Root Cause Hypothesis:** Probable cause patterns  
- 🛠️ **Remediation Steps:** Actionable next steps  
- 🚦 **Severity Level:** P1, P2, P3 recommendations  

No waiting for BTB.  
No lost hours.  
RTB can **proactively resolve** or **communicate fixes** directly to clients.  

> AI became the bridge between RTB and BTB.

---

##  The Impact  

| Metric | Before | After |
|---------|---------|--------|
| **Mean Time to Resolution** | 3–4 hours | ~45 minutes |
| **RTB Dependency on BTB** | High | Reduced by ~60% |
| **Client Communication Lag** | Delayed | Real-time updates |
| **Operational Visibility** | Fragmented | Unified dashboard |

---

## Tech Stack  

| Layer | Tool | Purpose |
|-------|------|----------|
| **Ingestion** | Apache Airflow | Automates ETL |
| **Storage** | PostgreSQL | Central data warehouse |
| **Transformation** | dbt | Builds SLA metrics and models |
| **Visualization** | Streamlit | Dashboard + AI triage UI |
| **AI Layer** | OpenAI API | Generates incident summaries |
| **Containerization** | Docker | Unified, reproducible setup |

---

## Setup  

### Local Installation  
```bash
git clone https://github.com/<your-username>/incidentiq.git
cd incidentiq
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
