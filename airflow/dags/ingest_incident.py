from datetime import datetime
import os
import pandas as pd
import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator

PG_CONN = {
    "host": "postgres",
    "port": 5432,
    "dbname": os.getenv("POSTGRES_DB", "incidentdb"),
    "user": os.getenv("POSTGRES_USER", "incident"),
    "password": os.getenv("POSTGRES_PASSWORD", "incidentpw"),
}

CSV_PATH = "/opt/airflow/data/incident_event_log.csv"
DATE_COLS = ["opened_at","sys_created_at","sys_updated_at","resolved_at","closed_at"]
BOOL_COLS = ["active","made_sla","knowledge","u_priority_confirmation"]
ALL_COLS = [
    "number","incident_state","active","reassignment_count","reopen_count",
    "sys_mod_count","made_sla","caller_id","opened_by","opened_at",
    "sys_created_by","sys_created_at","sys_updated_by","sys_updated_at",
    "contact_type","location","category","subcategory","u_symptom","cmdb_ci",
    "impact","urgency","priority","assignment_group","assigned_to","knowledge",
    "u_priority_confirmation","notify","problem_id","rfc","vendor","caused_by",
    "close_code","resolved_by","resolved_at","closed_at"
]

def ingest_uci():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Missing CSV at {CSV_PATH}")

    df = pd.read_csv(CSV_PATH,low_memory=False,parse_dates=DATE_COLS,dayfirst=True,)

#--Datacleaning and transformation steps--
    df = df.replace(to_replace=[r"^\s*$", r"^\?$", r"^null$", r"^none$", r"^nan$"],
        value=pd.NA,regex=True)

    
    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

   
    for c in BOOL_COLS:
        if c in df.columns:
            df[c] = (
                df[c]
                .astype(str)
                .str.strip()
                .str.lower()
                .map({"true": True, "false": False})
            )

    
    for col in ["impact", "urgency", "priority", "reassignment_count", "reopen_count", "sys_mod_count"]:
        if col in df.columns:
            # extract leading digits if present
            s = df[col].astype(str).str.extract(r"(\d+)")[0]
            df[col] = pd.to_numeric(s, errors="coerce").astype("Int64")

    keep = [c for c in ALL_COLS if c in df.columns]
    df = df[keep]

   
    for col in DATE_COLS:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: (x.to_pydatetime() if isinstance(x, pd.Timestamp) else None)
            )

    for col in ["impact", "urgency", "priority", "reassignment_count", "reopen_count", "sys_mod_count"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: int(x) if pd.notna(x) else None)

   
    df = df.astype(object).where(pd.notnull(df), None)

    # - Insert into Postgres --
    conn = psycopg2.connect(**PG_CONN)
    cur = conn.cursor()
    cols = ",".join(keep)
    placeholders = ",".join(["%s"] * len(keep))
    sql = f"INSERT INTO raw.uci_incident_events ({cols}) VALUES ({placeholders})"
    cur.executemany(sql, df.values.tolist())
    conn.commit()
    cur.close()
    conn.close()
    print(f"Ingested {len(df)} rows into raw.uci_incident_events")

with DAG(
    dag_id="ingest_incident_events",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["uci","ingest","postgres"],
) as dag:
    PythonOperator(task_id="ingest_uci", python_callable=ingest_uci)
