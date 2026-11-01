from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import text

def init_db():
    from backend import models
    Base.metadata.create_all(bind=engine)
    # Ensure migration columns exist on existing databases
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN resource VARCHAR(128) DEFAULT 'System / General'"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE approval_requests ADD COLUMN resource VARCHAR(128) DEFAULT 'System / General'"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE permissions ADD COLUMN description TEXT DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
