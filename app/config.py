# app/config.py
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app/data/streaming_history.db'
    str_datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    
    def __str__(self):
        return f"DATA_DIR={self.DATA_DIR}), BASE_DIR={self.BASE_DIR}), SQLALCHEMY_DATABASE_URI={self.SQLALCHEMY_DATABASE_URI})"


if __name__ == '__main__':
    print(Config())