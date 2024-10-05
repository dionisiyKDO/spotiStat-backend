from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
import os

from app.config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_size=20, max_overflow=0)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    import app.models
    Base.metadata.create_all(bind=engine)
    
    # manually drop table User
    # app.models.User.__table__.drop(bind=engine) 
    
    # manually change first entry of custom_id to 'dionisiy'
    # first_entry = db_session.query(app.models.User).first()
    # if first_entry:
    #     first_entry.custom_id = 'dionisiy'
    #     db_session.commit()
    
# Initialize user-specific DBs
def get_user_db(spotify_user_id):
    # Generate user-specific folder and database path
    user_folder = os.path.join("data", spotify_user_id)
    os.makedirs(user_folder, exist_ok=True)
    user_db_path = os.path.join(user_folder, "listening_history.db")
    
    # Create engine and session for the specific user
    user_engine = create_engine(f"sqlite:///{user_db_path}")
    user_db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=user_engine))
    return user_db_session