from fastapi import FastAPI
from dotenv import load_dotenv
import os

# ── Database setup ─────────────────────────────────────────────────────────────
from database import Base, engine
import models  # registers all models to SQLAlchemy

# Auto-creates all tables on startup — skips if already existing
Base.metadata.create_all(bind=engine)

# ── App ────────────────────────────────────────────────────────────────────────
load_dotenv()
app = FastAPI(title="BananaGuardAI API")


@app.get("/")
def root():
    return {"message": "BananaGuardAI Backend is running!"}


@app.get("/test-db")
def test_db():
    """Check that all tables exist in Supabase."""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return {
        "status": "Connected to Supabase!",
        "tables_found": tables
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)