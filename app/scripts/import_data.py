# scripts/import_data.py
import os

from app.database import SessionLocal, engine, Base
from app.services import bulk_import_history
from app.config import Config

def create_tables():
    """Creates tables if they don't exist"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
def process_folder(folder_path, username):
    db = SessionLocal()
    try:
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".json"):
                full_path = os.path.join(folder_path, file_name)
                print(f"Processing {full_path}...")
                bulk_import_history(db, full_path, username)
    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
    
    username = "dionisiy"
    data_dir = Config.DATA_DIR / username
    
    process_folder(data_dir, username)