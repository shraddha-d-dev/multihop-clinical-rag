import os
import sqlite3
import json
from dotenv import load_dotenv

DB_NAME=os.getenv("DB_NAME")
JSON_FILE_PATH=os.getenv("JSON_FILE_PATH")

def create_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trials (
            nct_id TEXT PRIMARY KEY,
            title TEXT,
            conditions TEXT,
            phases TEXT,
            enrollment_count INTEGER,
            start_date TEXT,
            completion_date TEXT,
            lead_sponsor TEXT
        )
    """)
    conn.commit()

def insert_trial(conn, study):
    protocol_mod = study.get('protocolSection', {})
    id_mod = protocol_mod.get('identificationModule', {})
    cond_mod = protocol_mod.get('conditionsModule', {})
    design_mod = protocol_mod.get('designModule', {})
    enroll_mod = design_mod.get('enrollmentInfo', {})
    status_mod = protocol_mod.get('statusModule', {})
    start_date = status_mod.get('startDateStruct', {})
    completion_date = status_mod.get('completionDateStruct', {})
    sponsor_mod = protocol_mod.get('sponsorCollaboratorsModule', {})
    lead_sponsor_mod = sponsor_mod.get('leadSponsor', {})

    conn.execute("""
        INSERT OR REPLACE INTO trials VALUES(?,?,?,?,?,?,?,?)
    """,(
        id_mod.get('nctId'),
        id_mod.get('briefTitle'),
        json.dumps(cond_mod.get('conditions', [])),
        json.dumps(design_mod.get('phases', [])),
        enroll_mod.get('count'),
        start_date.get('date'),
        completion_date.get('date'),
        lead_sponsor_mod.get('name')
    )
    )
    conn.commit()

def get_trials(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM trials')
    data = cursor.fetchall()
    print(data)


if __name__ == '__main__':

    db_name = DB_NAME
    conn = sqlite3.connect(db_name)
    
    create_schema(conn)

    with open(JSON_FILE_PATH, 'r') as f:
        studies = json.load(f)

    for idx,study in enumerate(studies):
        insert_trial(conn, study)
        print(f'Inserted study: {idx}')
    print(f'Loaded {len(studies)} studies into SQLite') 
    # 16713 excluding duplicates

    get_trials(conn)

    conn.close()