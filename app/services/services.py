# app/services.py
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import insert
from app.models import StreamingHistory
from app.schemas import StreamingHistoryCreate

def bulk_import_history(db: Session, file_path: str, username: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # 1. Transform raw dicts using Pydantic (Validate data)
        # We assume raw_data is a list of dicts
        valid_records = []
        for record in raw_data:
            # Inject username since it's not in the JSON usually
            record['username'] = username 
            
            # Pydantic validation (optional but recommended)
            # This handles type casting and missing fields automatically
            obj = StreamingHistoryCreate(**record) 
            valid_records.append(obj.model_dump())

        # 2. Bulk Insert (Much faster than adding one by one)
        # strict=False avoids stopping on duplicate errors if you configure that
        if valid_records:
            db.execute(insert(StreamingHistory), valid_records)
            db.commit()
            logging.info(f"Successfully imported {len(valid_records)} records from {file_path}")
            return True
            
    except Exception as e:
        logging.error(f"Error importing {file_path}: {e}")
        db.rollback()
        return False