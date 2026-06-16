import os
import boto3
import tempfile
from mangum import Mangum
from api.main import app

# ── S3 data download on cold start ──────────────────────
S3_BUCKET  = os.getenv("S3_BUCKET", "clinicalmind-data")
LOCAL_DATA = "/tmp/data"   # Lambda's only writable path

def download_data_from_s3():
    """
    Downloads SQLite db and FAISS index from S3 to /tmp.
    Only runs on cold start — stays in memory after that.
    """
    if os.path.exists(f"{LOCAL_DATA}/trial_data.db") and os.path.exists(f"{LOCAL_DATA}/models") :
        return   # already downloaded in this container

    os.makedirs(f"{LOCAL_DATA}/faiss_index", exist_ok=True)
    os.makedirs(f"{LOCAL_DATA}/models", exist_ok=True)

    s3 = boto3.client("s3")

    print("Cold start: downloading data from S3...")

    # Download SQLite
    s3.download_file(
        S3_BUCKET,
        "trial_data.db",
        f"{LOCAL_DATA}/trial_data.db"
    )

    # Download FAISS index files
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix='faiss_index/'):
        for obj in page.get("Contents", []):
            key = obj['Key']
            filename = key.split('/')[-1]
            s3.downlaod_file(S3_BUCKET, key, f'{LOCAL_DATA}/faiss_index/{filename}')

    # Download model for embedding
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix='models/'):
        for obj in page.get("Contents", []):
            key = obj['Key']
            relative_path = key[len("models/"):]
            if not relative_path:
                continue
            local_path = f"{LOCAL_DATA}/models/{relative_path}"
            # Create subdirectories if model has nested folders
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            s3.download_file(S3_BUCKET, key, local_path)
            print(f"Downloaded: {key}")

    
    # Point env vars to /tmp paths
    os.environ["DB_PATH"]   = f"{LOCAL_DATA}/trial_data.db"
    os.environ["INDEX_PATH"] = f"{LOCAL_DATA}/faiss_index"
    os.environ["EMBEDDINDS_MODEL_PATH"] = f"{LOCAL_DATA}/models"


    print("Data download complete")

# Run on cold start (module level = runs once per container)
download_data_from_s3()

# Mangum wraps FastAPI for Lambda
handler = Mangum(app, lifespan="off")